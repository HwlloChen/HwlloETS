from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QListWidget, QTextEdit, QPushButton, QCheckBox,
                             QListWidgetItem, QLabel, QLineEdit, QSpinBox,
                             QGroupBox, QFormLayout)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QTextCharFormat
import asyncio
import importlib
import os
from .log import Logger
from .adb import ADBController
from .config import Config
from utils.task_executor import TaskExecutor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 初始化logger
        self.logger = Logger().get_logger()
        self.setWindowTitle("HwlloETS")
        self.setMinimumSize(800, 600)
        
        # 初始化ADB控制器(但不自动连接)
        self.adb_controller = ADBController()
        
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # 左侧任务列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.task_list = QListWidget()
        self.start_button = QPushButton("开始执行")
        self.start_button.clicked.connect(self.start_tasks)
        left_layout.addWidget(self.task_list)
        left_layout.addWidget(self.start_button)
        layout.addWidget(left_widget, 1)
        
        # 创建日志显示控件
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        
        # 中间配置区域
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        
        # ADB配置组
        adb_group = QGroupBox("ADB配置")
        adb_form = QFormLayout(adb_group)
        self.adb_host = QLineEdit(Config().get("adb", "host"))
        self.adb_port = QSpinBox()
        self.adb_port.setRange(1, 65535)
        self.adb_port.setValue(Config().get("adb", "port"))
        adb_form.addRow("主机:", self.adb_host)
        adb_form.addRow("端口:", self.adb_port)
        
        # 截图配置组
        screenshot_group = QGroupBox("截图配置")
        screenshot_form = QFormLayout(screenshot_group)
        self.screenshot_fps = QSpinBox()
        self.screenshot_fps.setRange(1, 30)
        self.screenshot_fps.setValue(Config().get("screenshot", "fps"))
        screenshot_form.addRow("FPS:", self.screenshot_fps)

        # TTS配置组
        tts_group = QGroupBox("TTS配置")
        tts_form = QFormLayout(tts_group)
        self.tts_language = QLineEdit(Config().get("tts", "language"))
        tts_form.addRow("语言:", self.tts_language)

        # OCR配置组
        ocr_group = QGroupBox("OCR配置")
        ocr_form = QFormLayout(ocr_group)
        self.ocr_language = QLineEdit(Config().get("ocr", "language"))
        self.ocr_tesseract = QLineEdit(Config().get("ocr", "tesseract_cmd"))
        ocr_form.addRow("语言:", self.ocr_language)
        ocr_form.addRow("Tesseract路径:", self.ocr_tesseract)

        # 保存按钮
        save_button = QPushButton("保存配置")
        save_button.clicked.connect(self.save_config)
        
        # 添加到中间布局
        center_layout.addWidget(adb_group)
        center_layout.addWidget(screenshot_group)
        center_layout.addWidget(tts_group)
        center_layout.addWidget(ocr_group)
        center_layout.addWidget(save_button)
        center_layout.addStretch()
        
        # 修改主布局，添加中间配置区域
        layout.addWidget(left_widget, 1.5)
        layout.addWidget(center_widget, 2)
        layout.addWidget(self.log_display, 2)
        
        # 连接日志信号
        Logger().get_signal().new_log.connect(self.append_log)
        
        # 加载任务
        self.load_tasks()
        self.running = False

    def append_log(self, message):
        # 在日志之间添加空行
        if self.log_display.document().characterCount() > 0:
            self.log_display.append("")
        
        # 根据日志级别设置颜色
        format = QTextCharFormat()
        if "ERROR" in message:
            format.setForeground(QColor("#FF4444"))  # 红色
        elif "WARNING" in message:
            format.setForeground(QColor("#FFB300"))  # 橙色
        elif "INFO" in message:
            format.setForeground(QColor("#2196F3"))  # 蓝色
        elif "DEBUG" in message:
            format.setForeground(QColor("#757575"))  # 灰色
        else:
            format.setForeground(QColor("#FFFFFF"))  # 默认白色
        
        cursor = self.log_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(message + "\n", format)
        self.log_display.setTextCursor(cursor)
        self.log_display.ensureCursorVisible()

    def load_tasks(self):
        tasks_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'tasks')
        self.available_tasks = []  # 保存所有可用任务实例
        
        # 收集所有任务
        for file in os.listdir(tasks_dir):
            if file.endswith('.py') and file != '__init__.py' and file != 'base.py':
                module_name = f"tasks.{file[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and attr.__module__ == module.__name__:
                            task = attr()
                            self.available_tasks.append(task)
                except Exception as e:
                    Logger().get_logger().error(f"加载任务失败: {str(e)}")
        
        # 按优先级排序并显示（数值小的显示在前）
        self.available_tasks.sort(key=lambda x: x.priority)
        for task in self.available_tasks:
            item = QListWidgetItem()
            checkbox = QCheckBox(f"{task.name}")
            checkbox.setToolTip(f"{task.description} (优先级: {task.priority})")
            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, checkbox)

    def start_tasks(self):
        if not self.running:
            selected_tasks = []
            for i in range(self.task_list.count()):
                item = self.task_list.item(i)
                checkbox = self.task_list.itemWidget(item)
                if checkbox.isChecked():
                    task_name = checkbox.text()
                    # 从已加载的任务中查找匹配的任务
                    task = next((t for t in self.available_tasks if t.name == task_name), None)
                    if task:
                        # 创建新的任务实例
                        task_class = task.__class__
                        selected_tasks.append(task_class())
            
            if selected_tasks:
                self.running = True
                self.start_button.setText("停止执行")
                self.executor = TaskExecutor(selected_tasks, self.adb_controller)
                self.executor.task_completed.connect(self.on_task_completed)
                self.executor.all_tasks_completed.connect(self.on_all_tasks_completed)
                self.executor.start()
        else:
            self.stop_tasks()

    def stop_tasks(self):
        try:
            if hasattr(self, 'executor'):
                self.executor.stop()
                self.executor = None  # 使用赋值 None 替代 delattr
            self.running = False
            self.start_button.setText("开始执行")
            self.start_button.setEnabled(True)
            self.logger.info("任务已强制停止")
        except Exception as e:
            self.logger.error(f"停止任务时出错: {str(e)}")
            # 确保即使出错，界面状态也会被重置
            self.running = False
            self.start_button.setText("开始执行")
            self.start_button.setEnabled(True)

    def on_task_completed(self, task_name, success):
        status = "成功" if success else "失败"
        Logger().get_logger().info(f"任务 {task_name} 执行{status}")

    def on_all_tasks_completed(self):
        try:
            # 使用赋值 None 替代 delattr
            if hasattr(self, 'executor'):
                self.executor = None
            self.running = False
            self.start_button.setText("开始执行")
            self.start_button.setEnabled(True)
            self.logger.info("所有任务执行完成")
        except Exception as e:
            self.logger.error(f"完成任务处理时出错: {str(e)}")
            # 确保界面状态被重置
            self.running = False
            self.start_button.setText("开始执行")
            self.start_button.setEnabled(True)

    def save_config(self):
        config = Config()
        config.set("adb", "host", self.adb_host.text())
        config.set("adb", "port", self.adb_port.value())
        config.set("screenshot", "fps", self.screenshot_fps.value())
        config.set("tts", "language", self.tts_language.text())
        config.set("ocr", "language", self.ocr_language.text())
        config.set("ocr", "tesseract_cmd", self.ocr_tesseract.text())
        self.connect_adb()  # 重新连接ADB
        Logger().get_logger().info("配置已保存")

    def connect_adb(self):
        try:
            self.adb_controller = ADBController()
            if self.adb_controller.connect():
                Logger().get_logger().info("ADB连接成功")
            else:
                Logger().get_logger().error("ADB连接失败")
        except Exception as e:
            Logger().get_logger().error(f"ADB连接错误: {str(e)}")
