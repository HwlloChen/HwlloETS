import pytesseract
import cv2
from .log import Logger
from .config import Config

class OCRProcessor:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OCRProcessor, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = Logger().get_logger()
        self.config = Config()
        # 配置Tesseract
        pytesseract.pytesseract.tesseract_cmd = self.config.get("ocr", "tesseract_cmd")
        
    def preprocess_image(self, image):
        """预处理图片以提高OCR准确性"""
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 二值化
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        return binary

    def recognize_text(self, image) -> str:
        """识别图片中的文字"""
        try:
            # 预处理图片
            processed_img = self.preprocess_image(image)
            
            # 设置OCR选项
            custom_config = r'--oem 3 --psm 3 -l ' + self.config.get("ocr", "language")
            
            # 执行OCR
            text = pytesseract.image_to_string(processed_img, config=custom_config)
            
            # 清理文本
            text = text.strip()
            if text:
                self.logger.info(f"OCR识别结果: {text}")
                return text
            else:
                self.logger.warning("OCR未识别出文字")
                return ""
                
        except Exception as e:
            self.logger.error(f"OCR识别失败: {str(e)}")
            return ""
