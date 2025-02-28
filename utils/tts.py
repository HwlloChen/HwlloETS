from gtts import gTTS
import os
import sounddevice as sd
import soundfile as sf
from .log import Logger
from pydub import AudioSegment
import numpy as np
from .config import Config

class TTSManager:
    _instance = None
    CABLE_INPUT_ID = None
    
    def __init__(self):
        self.config = Config()
        devices = sd.query_devices()
        for device_id, device in enumerate(devices):
            # 匹配设备名称（兼容不同版本）
            if "CABLE Input" in device.get('name', '') and device['max_output_channels'] > 0:
                print(f"发现虚拟设备: ID={device_id}, 名称={device['name']}")
                self.CABLE_INPUT_ID = device_id
                break  # 选择第一个匹配项
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TTSManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.logger = Logger().get_logger()
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache', 'audio')
        os.makedirs(self.cache_dir, exist_ok=True)

    def text_to_speech(self, text, lang=None):
        if lang is None:
            lang = self.config.get("tts", "language")
        try:
            # 生成音频文件名
            filename_mp3 = os.path.join(self.cache_dir, f"{hash(text)}.mp3")
            filename_wav = os.path.join(self.cache_dir, f"{hash(text)}.wav")
            
            # 如果缓存中没有，则生成新的音频文件
            if not os.path.exists(filename_wav):
                tts = gTTS(text=text, lang=lang)
                tts.save(filename_mp3)
                audio = AudioSegment.from_mp3(filename_mp3)
                audio.export(filename_wav, format="wav")
                self.logger.info(f"已生成语音文件: {filename_wav}")
                os.remove(filename_mp3)
            
            return filename_wav
        except Exception as e:
            self.logger.error(f"TTS转换失败: {str(e)}")
            return None

    def play_audio(self, file_path):
        """播放音频到虚拟输出设备或默认输出设备"""
        try:
            # 读取音频文件
            data, samplerate = sf.read(file_path)
            
            if self.CABLE_INPUT_ID is not None:
                # 使用虚拟音频设备
                device_info = sd.query_devices(self.CABLE_INPUT_ID)
                device_id = self.CABLE_INPUT_ID
                self.logger.debug(f"使用虚拟音频设备(ID={device_id})")
            else:
                # 使用默认输出设备
                device_info = sd.query_devices(sd.default.device[1])
                device_id = None  # None 表示使用默认设备
                self.logger.debug("使用系统默认输出设备")
            
            # 获取设备通道数
            channels = device_info['max_output_channels']
            
            # 如果音频是单声道但设备支持双声道，转换为双声道
            if len(data.shape) == 1 and channels > 1:
                data = data.reshape(-1, 1)
                data = np.column_stack((data, data))
            
            # 播放音频
            self.logger.info("开始播放音频...")
            sd.play(data, samplerate, device=device_id)
            sd.wait()
            self.logger.info("音频播放完成")
            return True
            
        except Exception as e:
            self.logger.error(f"音频播放失败: {str(e)}")
            return False
