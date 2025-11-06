import cv2
import time
import torch
import numpy as np
import sys
import os
import gc
from datetime import datetime, timedelta
import re
from Flybook import send_message_to_feishu

# 设置环境变量减少内存占用
os.environ['CUDA_LAUNCH_BLOCKING'] = '0'
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'



# 延迟加载非核心模块
def lazy_import():
    global mss, Thread, Queue, win32api, win32con, random, pyperclip, subprocess
    import mss
    from threading import Thread
    from queue import Queue
    import win32api
    import win32con
    import random
    import pyperclip
    import subprocess
    return True

# 动态路径处理
def get_project_paths():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 模型路径
    model_path = os.path.join(base_dir, 'last.pt')
    if not os.path.exists(model_path):
        model_path = r'E:\F\POT\last.pt'  # 备用路径
    
    # yolov5路径
    yolo_path = os.path.join(base_dir, 'yolov5')
    if not os.path.exists(yolo_path):
        yolo_path = r'E:\F\POT\yolov5'  # 备用路径
    
    if yolo_path not in sys.path:
        sys.path.append(yolo_path)
        
    return model_path, yolo_path

# ---------------------- URL去重相关代码 ----------------------
CHECKED_URLS_FILE = 'checked_urls.txt'
MAX_CHECKED_URLS = 50  # 最大保存的URL数量
THIRTY_MINUTES = timedelta(minutes=10)

def load_checked_urls():
    """加载已检查的URL及其时间戳"""
    checked = {}
    if os.path.exists(CHECKED_URLS_FILE):
        try:
            with open(CHECKED_URLS_FILE, 'r') as f:
                for line in f:
                    if '\t' in line:
                        url, ts_str = line.strip().split('\t')
                        ts = datetime.fromisoformat(ts_str)
                        checked[url] = ts
        except Exception as e:
            print(f"加载URL文件出错: {e}")
    return checked

def save_checked_url(url):
    """保存URL及其时间戳，如果超过最大数量则删除最旧的条目"""
    checked = load_checked_urls()
    # 添加新的URL和当前时间
    checked[url] = datetime.now()
    if len(checked) > MAX_CHECKED_URLS:
        # 获取最旧的URL并删除
        oldest_url = min(checked, key=checked.get)
        del checked[oldest_url]
    # 将更新后的内容写入文件
    try:
        with open(CHECKED_URLS_FILE, 'w') as f:
            for url, ts in checked.items():
                f.write(f"{url}\t{ts.isoformat()}\n")
    except Exception as e:
        print(f"保存URL文件出错: {e}")
            
def is_url_recently_checked(url):
    """检查URL是否在设定时间内被处理过"""
    checked = load_checked_urls()
    if url in checked:
        return datetime.now() - checked[url] < THIRTY_MINUTES
    return False

# 定义需要过滤的关键词
FILTER_KEYWORDS = ['拍1', '拍2', '拍3', '拍4', '拍5', '[聊天记录]','JORDAN','专卖店','淘宝','.tb.cn','.Tb.cn']

def extract_urls(text):
    # 检查整个文本是否包含特定关键词
    if any(keyword in text for keyword in FILTER_KEYWORDS):
        print("检测到过滤关键词，跳过处理。")
        return 'error', -1
        
    # 提取密码
    inputpassword = 'error'  # 初始化密码为 "error"
    password_pattern = r'密\s*([a-zA-Z0-9\s]{6})'  # 支持空格并提取6个字符
    match = re.search(password_pattern, text)
    if match:
        inputpassword = match.group(1).replace(" ", "")  # 提取密码并去掉空格
    print(f"提取的密码: {inputpassword}")

    # 正则表达式匹配网址
    url_pattern = r'https?://[^\s]+|coupon.m.jd.com[^\s]+'
    urls = re.findall(url_pattern, text)

    # 处理每个 URL
    cleaned_urls = []
    for url in urls:
        if not url.startswith('https://') and not url.startswith('http://') and 'coupon.m.jd.com' in url:
            url = 'https://' + url
        # 清理URL
        cleaned_url = re.sub(r'Adidas.*$', '', url)  # 去掉包含"Adidas"后面的部分
        cleaned_url = cleaned_url.rstrip('/')  # 去掉 URL 末尾的斜杠
        cleaned_urls.append(cleaned_url)

    # 过滤 URL，确保没有重复项
    unique_urls = list(set(cleaned_urls))
    return inputpassword, unique_urls

class ScreenCapturer:
    def __init__(self, region):
        self.region = {
            "left": region[0],
            "top": region[1],
            "width": region[2],
            "height": region[3]
        }
        self._sct = None

    def grab_frame(self):
        try:
            if self._sct is None:
                self._sct = mss.mss()
            img = np.array(self._sct.grab(self.region))
            return img[:, :, :3] if img.shape[2] == 4 else img
        except Exception as e:
            print(f"屏幕捕获错误: {e}")
            # 重置mss实例
            self._sct = None
            return None
            
    def __del__(self):
        if self._sct:
            self._sct.close()

class YOLOv5Detector:
    def __init__(self, weights, device='cuda:0'):
        try:
            # 导入必要的YOLOv5模块
            from yolov5.models.common import DetectMultiBackend
            from yolov5.utils.torch_utils import select_device
            
            # 优化GPU内存使用
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            # 初始化设备和模型
            self.device = select_device(device)
            self.model = DetectMultiBackend(weights, device=self.device)
            self.model.eval()
            
            # 提前编译模型以提高性能
            if hasattr(torch.jit, "optimize_for_inference"):
                try:
                    self.model = torch.jit.optimize_for_inference(self.model)
                except:
                    pass
                    
            # 设置模型参数
            self.names = self.model.names
            self.img_size = 640
            
            # 预分配张量以避免重复分配
            self._tensor_cache = None
            print(f"YOLOv5模型加载成功: {weights}")
        except Exception as e:
            print(f"初始化YOLOv5模型出错: {e}")
            raise

    def detect(self, frame, img_size=None):
        if img_size is None:
            img_size = self.img_size
            
        try:
            # 导入NMS函数
            from yolov5.utils.general import non_max_suppression
            
            # 转换 BGR 为 RGB
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 调整大小
            img = cv2.resize(img, (self.img_size, self.img_size))
            
            # 复用张量内存
            if self._tensor_cache is None:
                self._tensor_cache = torch.zeros((1, 3, self.img_size, self.img_size), 
                                               device=self.device, dtype=torch.float32)
            
            # 转换为 PyTorch 张量
            tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
            self._tensor_cache[0].copy_(tensor.to(self.device))
            
            # 禁用梯度计算，加速推理
            with torch.no_grad():
                pred = self.model(self._tensor_cache)
                
            # 非极大值抑制
            return non_max_suppression(
                pred[0], 
                conf_thres=0.6,      # 提高置信度阈值
                iou_thres=0.5,       # 降低IoU阈值
                max_det=10,           # 限制最大检测数量
            )
        except Exception as e:
            print(f"检测过程出错: {e}")
            return []
    
    def calculate_click_position(self, xyxy):
        """计算检测框中心点坐标"""
        x1, y1, x2, y2 = xyxy
        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        return (center_x, center_y)

class ClickController:
    def __init__(self, cooldown=3.1, filter_window=5):
        self.last_click_time = time.time()
        self.cooldown = cooldown
        self.detection_queue = []  # 用于滤波的检测队列
        self.filter_window = filter_window
        self.clicked_targets = set()  # 新增集合跟踪已处理目标

    def can_click(self, target_id):
        # 检查目标是否已经被点击
        return target_id not in self.clicked_targets

    def mark_as_clicked(self, target_id):
        # 标记目标为已点击
        self.clicked_targets.add(target_id)

    def should_click(self, current_class):
        # 时间冷却检查
        if time.time() - self.last_click_time < self.cooldown:
            return False
        
        # 滤波逻辑：最近N帧中超过50%检测到才触发
        self.detection_queue.append(current_class)
        if len(self.detection_queue) > self.filter_window:
            self.detection_queue.pop(0)
        
        if sum(1 for c in self.detection_queue if c == current_class) / self.filter_window > 0.5:
            self.last_click_time = time.time()
            self.detection_queue.clear()
            return True
        return False

    def perform_click(self, x, y, region, right_click=False):
        x1 = int(region[0] + x)  # 将坐标映射回原始屏幕坐标
        y1 = int(region[1] + y)  # 将坐标映射回原始屏幕坐标

        # 使用截尾正态分布更合理
        def truncated_gauss(mu, sigma, min_val, max_val):
            while True:
                val = random.gauss(mu, sigma)
                if min_val <= val <= max_val:
                    return val

        if 0 < x1 < 3840 and 0 < y1 < 2160:  # 确保坐标在屏幕范围内
            try:
                # 执行鼠标移动
                win32api.SetCursorPos((x1, y1))
                down_time = truncated_gauss(mu=0.1, sigma=0.03, min_val=0.06, max_val=0.14)
                up_time = truncated_gauss(mu=0.1, sigma=0.02, min_val=0.07, max_val=0.13)

                # 执行点击动作
                if right_click:
                    # 右键点击
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x1, y1, 0, 0)
                    time.sleep(down_time)
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x1, y1, 0, 0)
                else:
                    # 左键点击
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x1, y1, 0, 0)
                    time.sleep(down_time)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x1, y1, 0, 0)

                time.sleep(up_time)
            except Exception as e:
                print(f"鼠标点击出错: {e}")

        return (x1, y1)  # 返回映射后的坐标

class AsyncCapture:
    def __init__(self, capturer):
        self.capturer = capturer
        self.queue = Queue(maxsize=1)  # 双缓冲队列设计
        self.running = True
        self.thread = Thread(target=self._capture_loop, daemon=True)  # 使用daemon=True确保程序退出时线程自动关闭
        self.thread.start()
 
    def _capture_loop(self):
        while self.running:
            try:
                frame = self.capturer.grab_frame()
                if frame is not None and self.queue.qsize() < 1:
                    if not self.queue.full():
                        self.queue.put(frame, block=False)
                else:
                    # 短暂休眠避免CPU占用过高
                    time.sleep(0.01)
            except Exception as e:
                print(f"异步捕获错误: {e}")
                time.sleep(0.1)  # 错误后短暂暂停
 
    def get_frame(self):
        try:
            return self.queue.get(block=False) if not self.queue.empty() else None
        except:
            return None
 
    def stop(self):
        self.running = False
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join(timeout=1.0)  # 最多等待1秒

def process_detections(frame, detections, detector, frame_height, frame_width, cvshow):
    valid_targets = []
    for det in detections:
        if det is not None and len(det):
            for *xyxy, conf, cls in det:
                try:
                    # 坐标映射回原始尺寸
                    x1 = int(xyxy[0].item() * frame_width / detector.img_size)
                    y1 = int(xyxy[1].item() * frame_height / detector.img_size)
                    x2 = int(xyxy[2].item() * frame_width / detector.img_size)
                    y2 = int(xyxy[3].item() * frame_height / detector.img_size)
                    
                    if cvshow:# 绘制检测框
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
                except Exception as e:
                    print(f"处理检测结果出错: {e}")
    return valid_targets

def memory_monitor():
    """内存监控和优化"""
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"内存使用: {memory_mb:.1f} MB")
        
        # 如果内存使用超过阈值，执行清理
        if memory_mb > 1024:  # 超过1GB时强制清理
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print("已执行内存清理")
    except ImportError:
        # psutil不可用时跳过监控
        pass
    except Exception as e:
        print(f"内存监控出错: {e}")



def main():
    # 延迟导入模块
    print("正在加载必要模块...")
    lazy_import()
    cvshow = True
    # 获取路径
    model_path, _ = get_project_paths()
    
    # 初始化核心组件
    print("初始化组件...")
    fps = 10# 从配置读取帧率设置
    frame_interval = 1.0 / fps  # 每帧理论间隔时间
    region = [10, 10, 450, 600]  # 屏幕捕获参数: left, top, width, height
    capturer = ScreenCapturer(region)
    
    try:
        # 初始化检测器
        print("加载YOLOv5模型...")
        detector = YOLOv5Detector(model_path, 'cuda:0' if torch.cuda.is_available() else 'cpu')
        
        # 初始化异步捕获和点击控制器
        async_capturer = AsyncCapture(capturer)
        click_controller = ClickController()
        
        # 性能监控变量
        prev_time = time.time()
        prev_frame = None
        wending = False
        yuszhi = 0
        memory_check_counter = 0
        
        print("程序启动完成，开始运行...")
        
        while True:
            try:
                # 获取帧
                time.sleep(frame_interval)
                frame = async_capturer.get_frame()
                if frame is None:
                    time.sleep(0.01)  # 短暂休眠避免CPU占用过高
                    continue
                
                # 强制内存连续性转换
                frame = np.ascontiguousarray(frame, dtype=np.uint8)
                
                
                # 执行检测
                detections = detector.detect(frame, detector.img_size)
                
                # 获取原始帧尺寸
                frame_height, frame_width, _ = frame.shape
                
                # 处理检测结果
                valid_targets = process_detections(frame, detections, detector, frame_height, frame_width, cvshow)
                
                # 过滤检测结果
                lianjie_targets = [t for t in valid_targets if t['class'] == 'connection']
                other_targets = [t for t in valid_targets if t['class'] != 'connection']
                
                if lianjie_targets:
                    max_lianjie = max(lianjie_targets, key=lambda x: x['bbox'][3])
                    filtered_targets = other_targets + [max_lianjie]
                else:
                    filtered_targets = valid_targets
                
                # 处理检测目标
                if filtered_targets:
                    for target in filtered_targets:
                        target_id = (target['class'], target['position'])  # 使用类名和位置作为唯一标识

                        if target['class'] == 'connection' and click_controller.can_click(target_id):
                            x, y = target['position']
                            click_controller.perform_click(x, y, region, right_click=True)
                            click_controller.mark_as_clicked(target_id)  # 标记为已点击
                            
                            # 点击"复制"
                            x2 = x + 20
                            y2 = y + 12
                            time.sleep(0.1)
                            x3, y3 = click_controller.perform_click(x2, y2, region, right_click=False)
                            #print(f"点击复制于坐标 {x3}, {y3}")
                            time.sleep(0.1)
                            # 处理复制的内容
                            copied_content = pyperclip.paste()
                            if copied_content:
                                #print(f"复制内容: {copied_content[:50]}..." if len(copied_content) > 50 else copied_content)
                                inputpassword, extracted_urls = extract_urls(copied_content)
                                
                                # 检查提取的URL
                                if extracted_urls == -1:
                                    wending = True
                                    continue
                                    
                                for url in extracted_urls:
                                    if is_url_recently_checked(url):
                                        print(f"跳过已处理URL: {url}")

                                    else:
                                        print(f"处理新URL: {url}")
                                        save_checked_url(url)  # 标记为已处理
                                    
                            else:
                                print("剪贴板为空，无内容复制")
                                
                            wending = True
                
                if cvshow:    # 计算和显示FPS
                    current_time = time.time()
                    fps = 1 / (current_time - prev_time)
                    prev_time = current_time

                    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.imshow("Optimized Detection", frame)
                
                # 定期内存监控
                memory_check_counter += 1
                if memory_check_counter >= 2000:  # 每100帧检查一次内存
                    memory_monitor()
                    memory_check_counter = 0
                
                # 检查退出条件
                if cv2.waitKey(1) == ord('q'):
                    break
                    
            except Exception as e:
                print(f"主循环错误: {e}")
                time.sleep(1)  # 错误后短暂暂停
                
    except Exception as e:
        print(f"初始化错误: {e}")
    finally:
        # 清理资源
        print("正在清理资源...")
        if 'async_capturer' in locals():
            async_capturer.stop()
        cv2.destroyAllWindows()
        
        # 释放内存
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        print("程序已退出")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"程序异常: {e}")
