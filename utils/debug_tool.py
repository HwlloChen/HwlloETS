import cv2
import numpy as np
from .screenshot import ScreenshotManager
from .config import Config
from .adb import ADBController

class DebugTool:
    def __init__(self):
        self.config = Config()
        self.adb = ADBController()
        if not self.adb.connect():
            raise Exception("无法连接到ADB设备")
        self.screenshot = ScreenshotManager(self.adb)
        self.scale = 0.5  # 设置缩放比例为50%

    def get_element_position(self, window_name="Debug Tool"):
        """交互式获取UI元素位置"""
        self.points = []
        
        def on_mouse(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                # 将缩放后的坐标转换回原始坐标
                real_x = int(x / self.scale)
                real_y = int(y / self.scale)
                self.points.append((real_x, real_y))
                print(f"点击位置: x={real_x}, y={real_y}")
        
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, on_mouse)
        
        while True:
            image = self.screenshot.get_screenshot(force_new=True)
            if image is not None:
                # 缩放图像
                display_image = cv2.resize(image, None, fx=self.scale, fy=self.scale)
                
                # 在图像上标记已点击的点
                for point in self.points:
                    # 将原始坐标转换为缩放后的坐标来显示
                    scaled_x = int(point[0] * self.scale)
                    scaled_y = int(point[1] * self.scale)
                    cv2.circle(display_image, (scaled_x, scaled_y), 3, (0, 0, 255), -1)
                    # 在点旁边显示原始坐标
                    cv2.putText(display_image, f"({point[0]},{point[1]})", 
                              (scaled_x + 5, scaled_y - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                cv2.imshow(window_name, display_image)
                
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # 按q退出
                break
            elif key == ord('c'):  # 按c清除点
                self.points = []
            elif key == ord('+') or key == ord('='):  # 按+增大缩放
                self.scale = min(1.0, self.scale + 0.1)
            elif key == ord('-'):  # 按-减小缩放
                self.scale = max(0.1, self.scale - 0.1)
        
        cv2.destroyAllWindows()
        return self.points

if __name__ == "__main__":
    # 调试代码示例
    tool = DebugTool()
    print("操作说明：")
    print("- 点击鼠标左键记录位置")
    print("- 按c清除所有点")
    print("- 按+/-调整窗口大小")
    print("- 按q退出程序")
    positions = tool.get_element_position()
    print("\n记录的位置:", positions)
