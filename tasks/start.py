from .base import BaseTask
import asyncio

class StartAppTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.name = "启动应用"
        self.description = "强制停止并重新启动ETS应用"
        self.priority = 1  # 修改为1，确保最先执行
        self.package_name = "com.ets100.secondary"
        self.activity = ".ui.main.MainActivity"

    async def execute(self, adb_controller, **kwargs):
        try:
            self.logger.info("开始执行启动任务")
            
            # 强制停止应用
            self.logger.info("正在停止应用...")
            adb_controller.shell(f'am force-stop {self.package_name}')
            await asyncio.sleep(2)
            
            # 启动应用
            self.logger.info("正在启动应用...")
            start_cmd = f'am start {self.package_name}/{self.activity}'
            adb_controller.shell(start_cmd)
            
            # 检查应用是否成功启动
            timeout = 5
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                current_app = adb_controller.shell('dumpsys window | grep mCurrentFocus')
                if current_app and self.package_name in current_app:
                    self.logger.info("应用启动成功")
                    return True
                await asyncio.sleep(0.5)
            
            self.logger.error("应用启动超时")
            return False
            
        except Exception as e:
            self.logger.error(f"启动任务执行失败: {str(e)}")
            return False
