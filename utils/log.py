import logging
from PySide6.QtCore import QObject, Signal
import sys
from datetime import datetime
import os

class LogSignal(QObject):
    new_log = Signal(str)

class LogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.signal = LogSignal()
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        msg = self.format(record)
        self.signal.new_log.emit(msg)

class Logger:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = logging.getLogger('HwlloETS')
        self.logger.setLevel(logging.DEBUG)
        
        # 创建日志目录
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # GUI处理器
        self.gui_handler = LogHandler()
        self.gui_handler.setLevel(logging.INFO)
        
        # 文件处理器
        log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # 设置格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(self.gui_handler)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger

    def get_signal(self):
        return self.gui_handler.signal
