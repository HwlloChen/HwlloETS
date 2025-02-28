from PySide6.QtCore import QThread, Signal
import asyncio
from .log import Logger

class TaskExecutor(QThread):
    task_completed = Signal(str, bool)
    all_tasks_completed = Signal()
    
    def __init__(self, tasks, adb_controller):
        super().__init__()
        self.tasks = tasks
        self.adb_controller = adb_controller
        self.logger = Logger().get_logger()
        self._running = True

    def stop(self):
        self._running = False
        self.logger.info("正在停止任务...")
        # 强制退出
        self.terminate()  # 强制终止线程
        self.wait()      # 等待线程完全停止
        self.adb_controller.disconnect()  # 确保断开ADB连接
        self.all_tasks_completed.emit()   # 发送任务完成信号

    def run(self):
        try:
            asyncio.run(self.execute_tasks())
        except:
            # 捕获所有异常，确保在强制停止时不会产生未处理的异常
            pass

    async def execute_tasks(self):  # 将原来run方法中的execute_tasks移出来
        # 确保ADB已连接
        if not self.adb_controller.connect():
            self.logger.error("无法连接到ADB设备，任务执行终止")
            self.all_tasks_completed.emit()
            return
        
        try:
            sorted_tasks = sorted(
                [t for t in self.tasks if t is not None],
                key=lambda x: x.priority
            )
            
            for task in sorted_tasks:
                if not self._running:
                    self.logger.info("任务执行被用户终止")
                    break
                    
                try:
                    result = await task.execute(adb_controller=self.adb_controller)
                    self.task_completed.emit(task.name, result)
                    if task != sorted_tasks[-1] and self._running:
                        self.logger.info("等待5秒后执行下一个任务...")
                        await asyncio.sleep(5)
                except Exception as e:
                    self.logger.error(f"任务执行出错: {str(e)}")
                    self.task_completed.emit(task.name, False)
        
        finally:
            if self._running:  # 只有在正常结束时才发送信号
                self.adb_controller.disconnect()
                self.all_tasks_completed.emit()
