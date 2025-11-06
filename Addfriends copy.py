import cv2
import time
import torch
import numpy as np
import sys
import os
import tkinter as tk
from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import non_max_suppression
from yolov5.utils.torch_utils import select_device
from yolov5.utils.augmentations import letterbox  # 新增导入
import mss
from threading import Thread
from queue import Queue
import win32api
import win32con
import random
import pyperclip
import pyautogui
from datetime import datetime

# 添加 yolov5 项目路径到 sys.path
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "yolov5"))
sys.path.insert(0, project_path)

class ScreenCapturer:
    def __init__(self, region):
        self.region = {
            "left": region[0],
            "top": region[1],
            "width": region[2],
            "height": region[3]
        }

    def grab_frame(self):
        with mss.mss() as sct:  # 每次调用创建新实例
            img = np.array(sct.grab(self.region))
            return img[:, :, :3] if img.shape[2] == 4 else img

class YOLOv5Detector:
    # 加载 YOLOv5 模型
    def __init__(self, weights, device='cuda:0'):
        self.device = select_device(device)#自动选择可用的计算设备（CPU 或 GPU）
        self.model = DetectMultiBackend(weights, device=self.device)
        self.model.eval()
        self.names = self.model.names # 类别名称映射
        self.img_size = 640
        self.pad = (0, 0, 0, 0)  # 新增：记录填充量(左,右,上,下)
        self.scale = 1.0         # 新增：记录实际缩放比例

    def detect(self, frame,cicun):
        # 转换 BGR 为 RGB
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
         # 调整大小为 640x640（YOLOv5 默认输入尺寸）
        img = cv2.resize(img, (self.img_size, self.img_size))
        # 转换为 PyTorch 张量并归一化到 [0,1]# 将输入数据移动到和模型相同的设备上
        tensor = torch.from_numpy(img / 255.0).permute(2, 0, 1).float().unsqueeze(0).to(self.device)

        # 禁用梯度计算，加速推理
        with torch.no_grad():
            pred = self.model(tensor)
        # 调整 NMS 的参数，避免多余的框
        return non_max_suppression(pred[0], conf_thres=0.4, iou_thres=0.4)
    
    def calculate_click_position(self, xyxy):
        """计算检测框中心点坐标"""
        x1, y1, x2, y2 = xyxy
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        print(f"x：{center_x},y:{center_y}")
        return (center_x, center_y)

class ClickController:
    def __init__(self, cooldown=3.1, filter_window=5):
        self.last_click_time = time.time()
        self.cooldown = cooldown
        self.detection_queue = []  # 用于滤波的检测队列
        self.filter_window = filter_window

    #current_class 参数表示当前检测到的类别
    def should_click(self, current_class):
        # 时间冷却检查
        if time.time() - self.last_click_time < self.cooldown:
            return False
        
        # 滤波逻辑：最近N帧中超过50%检测到才触发
        self.detection_queue.append(current_class)
        #如果检测队列的长度超过了滤波窗口的大小 self.filter_window，则移除队列中最早的元素，以保持队列的长度不超过窗口大小。
        if len(self.detection_queue) > self.filter_window:
            self.detection_queue.pop(0)
        
        if sum(1 for c in self.detection_queue if c == current_class) / self.filter_window > 0.5:
            self.last_click_time = time.time()
            self.detection_queue.clear()
            return True
        return False

    #鼠标点击控制功能
    def perform_click(self, x, y, region):
        x1 = int(region[0] + x)  # 将坐标映射回原始屏幕坐标
        y1 = int(region[1] + y)  # 将坐标映射回原始屏幕坐标
        # 使用截尾正态分布更合理
        def truncated_gauss(mu, sigma, min_val, max_val):
            while True:
                val = random.gauss(mu, sigma)
                if min_val <= val <= max_val:
                    return val
        if x1 >0 and y1 > 0 and x1 < 3840 and y1 < 2160:  # 确保坐标在屏幕范围内
            # 执行鼠标移动
            win32api.SetCursorPos((x1, y1))
            down_time = truncated_gauss(mu=0.1, sigma=0.03, min_val=0.06, max_val=0.14)
            up_time = truncated_gauss(mu=0.1, sigma=0.02, min_val=0.07, max_val=0.13)
            # 执行点击动作
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x1, y1, 0, 0)
            time.sleep(down_time)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x1, y1, 0, 0)
            time.sleep(up_time)
        return (x1, y1)  # 返回映射后的坐标

# ---------------------- 异步捕获类 ----------------------
class AsyncCapture:
    def __init__(self, capturer):
        self.capturer = capturer
        self.queue = Queue(maxsize=2)# 双缓冲队列设计
        self.running = True
        self.thread = Thread(target=self._capture_loop) # 独立采集线程
        self.thread.start()
 
    def _capture_loop(self):
        while self.running:
            frame = self.capturer.grab_frame()
            if self.queue.qsize() < 2:
                self.queue.put(frame)
 
    def get_frame(self):
        return self.queue.get() if not self.queue.empty() else None
 
    def stop(self):
        self.running = False
        self.thread.join()

# ---------------------- 异步捕获类 ----------------------
def process_detections(frame, detections, detector, frame_height, frame_width):
    valid_targets = []
    for det in detections:
        if det is not None and len(det):
            for *xyxy, conf, cls in det:
                # 坐标映射回原始尺寸
                x1 = int(xyxy[0] * frame_width / detector.img_size)
                y1 = int(xyxy[1] * frame_height / detector.img_size)
                x2 = int(xyxy[2] * frame_width / detector.img_size)
                y2 = int(xyxy[3] * frame_height / detector.img_size)
                
                # 绘制检测框
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                cv2.putText(
                    frame, 
                    f"{detector.names[int(cls)]} {conf:.2f}",
                    (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, (0, 255, 0), 1
                )
                valid_targets.append({
                    'class': detector.names[int(cls)],
                    'confidence': conf.item(),
                    'position': ((x1+x2)//2, (y1+y2)//2),
                    'bbox': [x1, y1, x2, y2]
                })
    return valid_targets

# ----------------------复制粘贴----------------------            
def process_phone_numbers(file_path):
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        if lines:
            # 获取第一行电话号码
            first_phone_number = lines[0].strip()
            # 复制到剪贴板
            pyperclip.copy(first_phone_number)
            print(f"已复制电话号码: {first_phone_number} 到剪贴板。")

            # 删除第一行
            remaining_lines = lines[1:]

            # 更新文件内容
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(remaining_lines)
            # 等待一段时间，让用户可以将焦点切换到需要粘贴的位置
            time.sleep(5)
            # 模拟按下 Ctrl + V 组合键进行粘贴
            pyautogui.hotkey('ctrl', 'v')
            print("已模拟按下 Ctrl + V 进行粘贴。")
        else:
            print("文件中没有电话号码。")

    except FileNotFoundError:
        print("错误: 文件未找到。")
    except Exception as e:
        print(f"发生未知错误: {e}")

def main():
    # 初始化模块
    # 从配置读取帧率设置
    fps = 30
    frame_interval = 1.0 / fps  # 每帧理论间隔时间
    phone_numbers_file_path = 'phone_numbers.txt'  # 请替换为你的实际文件路径
    region = [10, 100, 1000, 1500]# 屏幕捕获参数# left, top, width, height
    capturer = ScreenCapturer(region)# 屏幕捕获参数# left, top, width, height
    detector = YOLOv5Detector(r'C:\Users\liaohf\Desktop\LHF_2025\yolov5_2.0\runs\train\exp\weights\last.pt', 'cuda:0')# 模型参数

    async_capturer = AsyncCapture(capturer)#异步处理架构
    #过滤器
    click_controller = ClickController()

    
    prev_time = time.time()
    # 步骤计数器
    step = 0
    break_step = 0
    target_classes = ['lxren1', 'addfriend', 'zhao', 'search','tjia','tru','send']# 目标类列表
    break_classes = ['back', 'back',  'back', 'back', 'back', 'weixin', 'over']# 终止类列表
    last_valid_time = time.time()  # 初始化计时器
    try:
        while True:
            start_time = time.time()
            frame = async_capturer.get_frame()
            if frame is None:
                continue
            # 新增：强制内存连续性转换
            frame = np.ascontiguousarray(frame, dtype=np.uint8)
            detections = detector.detect(frame,detector.img_size)
            # 获取原始帧尺寸
            frame_height, frame_width, _ = frame.shape
            #---------------------- 处理检测结果---------------------- 
            valid_targets=process_detections(frame, detections, detector, frame_height, frame_width)
            if 0:
                for target in valid_targets:
                    #****************第一阶梯**************防止点到"我"的界面那里*************
                    if step == 0:
                        if target['class'] == 'lxren0' or target['class'] == 'lxren1':
                            if click_controller.should_click(target['class']):
                                x, y = target['position']
                                x1, y1 =click_controller.perform_click(x, y, region)
                                print(f"Clicked on__ {target['class']} __at {x1}, {y1}")
                                last_valid_time = time.time()
                                step += 1  # 进入下一阶段
                     #****************第二阶梯**************顺序点击*************************
                    elif step >0 and step <7:
                        if target['class'] == target_classes[step]:
                            if click_controller.should_click(target['class']):
                                x, y = target['position']
                                x1, y1 = click_controller.perform_click(x, y, region)
                                print(f"Clicked on__ {target['class']} __at {x1}, {y1}")
                                if target['class'] == 'zhao':
                                    process_phone_numbers(phone_numbers_file_path)
                                last_valid_time = time.time()
                                step += 1  # 进入下一阶段
                    elif step ==7:
                        if target['class'] == break_classes[break_step]:
                            if click_controller.should_click(target['class']):
                                x, y = target['position']
                                x1, y1 = click_controller.perform_click(x, y, region)
                                print(f"Clicked on__ {target['class']} __at {x1}, {y1}")
                                break_step += 1 
                                last_valid_time = time.time()
                                if break_classes[break_step] == 'over':
                                    break_step = 0
                                    step = 0
                                    print("初始化返回已完成所有步骤。")

            if time.time() - last_valid_time > 1000:
                timestamp = int(time.time())
                print(f"{timestamp}:超时！未检测到目标，截图保存")
                if frame is not None:
                    cv2.waitKey(500)
                    cv2.imwrite(f'timeout/timeout_{timestamp}.jpg', frame)
                last_valid_time = time.time()  # 重置计时器
                step = 7
            #---------------------- 处理检测结果----------------------
            # 显示 FPS
            current_time = time.time()
            fps = 1 / (current_time - prev_time)
            prev_time = current_time
            cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            processing_time = time.time() - start_time
            sleep_time = max(0, frame_interval - processing_time)
            time.sleep(sleep_time)  # 动态调整休眠时
            cv2.imshow("Optimized Detection", frame)
            if cv2.waitKey(1) == ord('q'):
                break
    finally:
        async_capturer.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()