from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from .config import Config
from .log import Logger
import os

class ADBController:
    def __init__(self):
        self.config = Config()
        self.logger = Logger().get_logger()
        self.device = None
        self._load_adb_keys()

    def _load_adb_keys(self):
        """加载ADB密钥"""
        self.signer = None
        try:
            adbkey_path = os.path.expanduser('~/.android/adbkey')
            if os.path.exists(adbkey_path):
                with open(adbkey_path) as f:
                    priv = f.read()
                with open(adbkey_path + '.pub') as f:
                    pub = f.read()
                self.signer = PythonRSASigner(pub, priv)
        except Exception as e:
            self.logger.warning(f"无法加载ADB密钥: {str(e)}")

    def connect(self):
        """连接到ADB设备"""
        try:
            host = self.config.get("adb", "host")
            port = self.config.get("adb", "port")
            
            self.device = AdbDeviceTcp(host, port, default_transport_timeout_s=9.)
            
            # 尝试连接
            self.device.connect(rsa_keys=[self.signer] if self.signer else None, auth_timeout_s=5)
            self.logger.info(f"已连接到 {host}:{port}")
            return True
            
        except Exception as e:
            self.logger.error(f"ADB连接失败: {str(e)}")
            self.device = None
            return False

    def disconnect(self):
        """断开ADB连接"""
        if self.device:
            try:
                self.device.close()
                self.device = None
                self.logger.info("ADB连接已断开")
            except Exception as e:
                self.logger.error(f"断开ADB连接失败: {str(e)}")

    def shell(self, cmd):
        """执行shell命令"""
        if not self.device:
            self.logger.error("ADB未连接")
            return None
        
        try:
            return self.device.shell(cmd)
        except Exception as e:
            self.logger.error(f"执行命令失败 '{cmd}': {str(e)}")
            return None

    def tap(self, x, y):
        """模拟点击"""
        return self.shell(f'input tap {x} {y}')

    def swipe(self, x1, y1, x2, y2, duration=500):
        """模拟滑动"""
        return self.shell(f'input swipe {x1} {y1} {x2} {y2} {duration}')

    def screencap(self):
        """截图"""
        if not self.device:
            return None
        try:
            return self.device.shell('screencap -p', decode=False)
        except Exception as e:
            self.logger.error(f"截图失败: {str(e)}")
            return None
