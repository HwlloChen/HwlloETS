from .base import BaseTask
import asyncio
from utils.screenshot import ScreenshotManager
from utils.ocr import OCRProcessor
from utils.tts import TTSManager
import numpy as np
import os

class HomeworkTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.name = "听说作业"
        self.description = "自动完成所有作业集中的课文听说作业"
        self.priority = 10  # 调整为较大的数值，在启动应用后执行
        
        # 定义UI元素位置
        self.tab_homework = {
            'description': '作业选项卡',
            'type': 'position',
            'x': 616,  # 从左往右第四个选项卡的x坐标
            'y': 1532  # 底部导航栏的y坐标
        }
        
        self.first_todo = {
            'description': '第一个待完成作业',
            'type': 'position',
            'x': 742,
            'y': 992
        }
        
        self.start_homework = {
            'description': '开始做作业按钮',
            'type': 'position',
            'x': 454,  # 屏幕中央
            'y': 1528  # 底部按钮位置
        }
        
        self.wait_for_loaded = {
            'description': '等待作业加载完成时检查关键点颜色的位置',
            'type': 'position',
            'x': 268,
            'y': 1472
        }
        
        self.determine_homework_type = {
            'description': '判断作业类型时检查关键点颜色的位置',
            'type': 'position',
            'x': 826,
            'y': 1548
        }
        
        self.pause_button = {
            'description': '暂停跟读按钮',
            'type': 'position',
            'x': 458,
            'y': 1434
        }
        
        self.fastread_button = {
            'description': '速读按钮',
            'type': 'position',
            'x': 200,
            'y': 1408
        }
        
        self.playing_checkpoints = [(463, 1450), (436, 1411)] # 如果两个点都为纯白，则判定为正在播放
        
        '''
        "range": 定义矩形范围
            "top": 最高处y坐标
            "bottom": 最低处y坐标
            "left": 最左侧x坐标
            "right": 最右侧x坐标
        '''
        self.follow_sentences_range = {
            'description': '一个矩形范围，定义跟读模式中文本的范围',
            'type': 'range',
            'top': 245,
            'bottom': 1243,
            'left': 146,
            'right': 844
        }
        
        self.follow_sentences_step_height = 29 # 每29像素拼接一次
        
        self.stop_recording_button = {
            'description': '停止录音按钮',
            'type': 'position',
            'x': 450,
            'y': 1432
        }
        
        self.finish_button = {
            'description': '完成作业按钮',
            'type': 'position',
            'x': 652,
            'y': 1556
        }
        
        # 添加调试图片保存路径
        self.debug_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'debug', 'ocr_images')
        os.makedirs(self.debug_dir, exist_ok=True)
        
        self.ocr = OCRProcessor()  # 初始化OCR处理器
        self.tts = TTSManager()

    async def execute(self, adb_controller, **kwargs):
        screenshot_mgr = ScreenshotManager(adb_controller)
        try:
            self.logger.info("开始执行听说作业任务")
            
            # 1. 点击作业选项卡
            self.logger.info("正在切换到作业页面...")
            adb_controller.tap(self.tab_homework['x'], self.tab_homework['y'])
            await asyncio.sleep(5)  # 等待页面加载
            
            # 2. 点击第一个"去完成"按钮
            self.logger.info("正在进入第一个作业...")
            adb_controller.tap(self.first_todo['x'], self.first_todo['y'])
            await asyncio.sleep(5)
            
            # 3. 点击"做作业"按钮
            
            homework_type = '' # follow 或者 read
            
            self.logger.info("正在打开作业...")
            adb_controller.tap(self.start_homework['x'], self.start_homework['y'])
            await asyncio.sleep(1)
            
            # 4. 等待加载完成
            self.logger.info("等待作业加载完成...")
            times = 0
            while True:
                screen = screenshot_mgr.get_screenshot(force_new=True)
                if screen is not None:
                    # 获取指定位置的颜色（BGR格式）
                    color = screen[self.wait_for_loaded['y'], self.wait_for_loaded['x']]
                    # 检查是否为纯白色 (255, 255, 255)
                    if np.array_equal(color, [255, 255, 255]):
                        times+=1
                        if(times >= 3): # 三次以上判定为成功
                            self.logger.info("作业加载完成")
                            break
                await asyncio.sleep(0.2)  # 每0.2秒检查一次
                
            # 5. 判断作业类型
            screen = screenshot_mgr.get_screenshot(force_new=True)
            if screen is not None:
                # 获取指定位置的颜色（BGR格式）
                color = screen[self.determine_homework_type['y'], self.determine_homework_type['x']]
                # 检查是否为纯白色 (255, 255, 255)
                if np.array_equal(color, [255, 255, 255]):
                    homework_type = 'follow'
                else:
                    homework_type = 'read'
                self.logger.info(f"作业类型：{"跟读" if homework_type == 'follow' else "朗读"}")
                
            # 6. 跟读处理逻辑
            if homework_type == 'follow':
                # 6.1 暂停跟读和切换速读
                adb_controller.tap(self.pause_button['x'], self.pause_button['y'])
                
                screen = screenshot_mgr.get_screenshot(force_new=True)
                if screen is not None:
                    # 获取指定位置的颜色（BGR格式）
                    color = screen[self.fastread_button['y'], self.fastread_button['x']]
                    # 检查是否蓝色 (48, 138, 245)
                    if not np.array_equal(color, [245, 138, 48]):
                        adb_controller.tap(self.fastread_button['x'], self.fastread_button['y'])
                        self.logger.info("切换速读")
                await asyncio.sleep(1)
                
                # 6.2 开始朗读
                adb_controller.tap(self.pause_button['x'], self.pause_button['y'])
                
                # 6.3 依次朗读
                while True:
                    # 6.3.1 等待评分完成（等对面入机朗读）
                    while True:
                        screen = screenshot_mgr.get_screenshot(force_new=True)
                        if screen is not None:
                            # 获取指定位置的颜色（BGR格式）
                            color1 = screen[self.playing_checkpoints[0][1], self.playing_checkpoints[0][0]]
                            color2 = screen[self.playing_checkpoints[1][1], self.playing_checkpoints[1][0]]
                            # 检查是否为纯白色 (255, 255, 255)
                            if np.array_equal(color1, [255, 255, 255]) and np.array_equal(color2, [255, 255, 255]):
                                self.logger.info("对方朗读开始")
                                break
                        await asyncio.sleep(0.07)  # 每0.07秒检查一次
                    # 6.3.2 OCR识别内容
                    # 6.3.2.1 选择图片的正确区域
                    
                    screen = screenshot_mgr.get_screenshot(force_new=True)
                    if screen is None:
                        continue
                        
                    # 初始化方形选择器
                    head_y = self.follow_sentences_range['top']
                    tail_y = head_y
                    left_x = self.follow_sentences_range['left']
                    right_x = self.follow_sentences_range['right']
                    bottom_limit = self.follow_sentences_range['bottom']
                    
                    image_to_ocr = None
                    while tail_y <= bottom_limit:
                        tail_y += self.follow_sentences_step_height
                        # 获取当前矩形区域
                        roi = screen[head_y:tail_y, left_x:right_x]
                        
                        # 检查是否有异常颜色 - 使用向量化操作
                        unexpected_colors = np.array([
                            [248, 253, 245],  # 浅绿色 (BGR)
                            [88, 219, 29],    # 绿色 (BGR)
                            [2, 167, 255],    # 黄色 (BGR)
                            [82, 82, 255],    # 红色 (BGR)
                            [0, 0, 0]         # 纯黑色
                        ])
                        
                        # 使用向量化操作检查颜色
                        has_unexpected_color = False
                        for color in unexpected_colors:
                            if np.any(np.all(roi == color, axis=2)):
                                has_unexpected_color = True
                                break
                        
                        if has_unexpected_color:
                            # self.logger.info(f"坐标{head_y}到{tail_y}不行")
                            head_y = tail_y
                            continue
                        
                        if tail_y - head_y >= 2 * self.follow_sentences_step_height:
                            # 首先检查当前区域是否包含非白色像素
                            has_non_white = not np.all(roi == [255, 255, 255])
                            
                            if has_non_white:  # 只有当前区域包含非白色像素时才检查上方区域
                                # 检查向上两倍step_height的范围是否都是白色
                                upper_region = screen[tail_y - 2 * self.follow_sentences_step_height:tail_y, left_x:right_x]
                                # 使用向量化操作检查白色
                                all_white_above = np.all(upper_region == [255, 255, 255])

                                if all_white_above:
                                    image_to_ocr = roi.copy()
                                    self.logger.info(f"找到文本区域：y1={head_y}, y2={tail_y}")
                                    break
                            else:
                                head_y = tail_y  # 如果当前区域全白，直接移动到下一个区域
                    
                    # 6.3.2.2 执行OCR识别
                    text = None
                    if image_to_ocr is not None:
                        text = self.ocr.recognize_text(image_to_ocr)
                        text = text.split('\n', 1)[-1]
                        text = text.replace('\n', ' ')
                        text = text.replace('|', 'I')
                        if text:
                            self.logger.info(f"当前句子: {text}")
                        else:
                            self.logger.warning("句子识别失败")
                    else:
                        self.logger.warning("未找到合适的文本区域")
                    
                    # 6.3.3 将识别出的文本转化为语音文件并播放
                    audio_file = self.tts.text_to_speech(text)
                    
                    while True:
                        screen = screenshot_mgr.get_screenshot(force_new=True)
                        if screen is not None:
                            # 获取指定位置的颜色（BGR格式）
                            color = screen[self.stop_recording_button['y'], self.stop_recording_button['x']]
                            if np.array_equal(color, [67, 57, 255]):
                                self.logger.info("我方朗读开始")
                                break
                        await asyncio.sleep(0.05)  # 每0.05秒检查一次
                    
                    if audio_file:
                        if self.tts.play_audio(audio_file):
                            self.logger.info("语音播放成功")
                        else:
                            self.logger.error("语音播放失败")
                            
                    screen = screenshot_mgr.get_screenshot(force_new=True)
                    if screen is not None:
                        # 获取指定位置的颜色（BGR格式）
                        color = screen[self.finish_button['y'], self.finish_button['x']]
                        # 检查是否蓝色 (48, 138, 245)
                        if np.array_equal(color, [255, 143, 54]):
                            adb_controller.tap(self.finish_button['x'], self.finish_button['y'])
                            self.logger.info("开始下一个子作业")

            # TODO: 后续步骤将继续完善...
            
            return True
            
        except Exception as e:
            self.logger.error(f"听说作业执行失败: {str(e)}")
            return False
