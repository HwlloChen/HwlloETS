import time
from PIL import Image
import io
import numpy as np
import cv2
from .adb import ADBController
from .log import Logger
from .config import Config

class ScreenshotManager:
    def __init__(self, adb_controller: ADBController):
        self.config = Config()
        self.adb = adb_controller
        self.fps = self.config.get("screenshot", "fps")
        self.running = False
        self.logger = Logger().get_logger()
        self.last_screenshot = None
        self.last_screenshot_time = 0

    def get_screenshot(self, force_new=False, max_age_ms=200):
        """获取截图
        force_new: 是否强制获取新截图
        max_age_ms: 上一次截图的最大有效期(毫秒)
        """
        current_time = time.time() * 1000
        
        if not force_new and self.last_screenshot is not None:
            if current_time - self.last_screenshot_time < max_age_ms:
                return self.last_screenshot

        screenshot_bytes = self.adb.screencap()
        if screenshot_bytes:
            try:
                # 转换为PIL图像
                image = Image.open(io.BytesIO(screenshot_bytes))
                # 转换为OpenCV格式
                cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
                self.last_screenshot = cv_image
                self.last_screenshot_time = current_time
                return cv_image
            except Exception as e:
                self.logger.error(f"截图处理失败: {str(e)}")
                return None
        return None

    def start_capture(self):
        """开始连续截图"""
        self.running = True
        while self.running:
            self.get_screenshot(force_new=True)
            time.sleep(1/self.fps)

    def stop_capture(self):
        """停止连续截图"""
        self.running = False
