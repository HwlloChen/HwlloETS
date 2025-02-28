import json
import os
from .log import Logger


class Config:
    _instance = None
    DEFAULT_CONFIG = {
        "adb": {
            "host": "127.0.0.1",
            "port": 16384
        },
        "screenshot": {
            "fps": 5
        },
        "tts": {
            "language": "en"
        },
        "ocr": {
            "language": "eng",
            "tesseract_cmd": r"D:\Program Files\Tesseract-OCR\tesseract.exe"
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = Logger().get_logger()
        self.config_path = os.path.join(os.path.dirname(
            os.path.dirname(__file__)), 'config.json')
        self.config = self._load_config()

    def _load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.info("配置文件不存在，创建默认配置")
                self._save_config(self.DEFAULT_CONFIG)
                return self.DEFAULT_CONFIG
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            return self.DEFAULT_CONFIG

    def _save_config(self, config):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}")
            return False

    def get(self, section, key=None):
        if key is None:
            return self.config.get(section, {})
        return self.config.get(section, {}).get(key)

    def set(self, section, key, value):
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        return self._save_config(self.config)
