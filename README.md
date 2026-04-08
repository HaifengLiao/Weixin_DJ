# 微信DJ

通过训练模型yoloV5识别微信信息进行复制处理

## 环境安装

### 1. 创建虚拟环境
```bash
cd /d "d:\2026_P\Weixin_DJ"
python -m venv venv
```

### 2. 激活虚拟环境并安装依赖
```bash
# Windows
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. 运行脚本
```bash
python Test_speek_2.0.1.py
```

或直接运行批处理文件：
```
聊天窗口监控.bat
```

## 依赖说明

- opencv: 图像处理
- torch: PyTorch深度学习框架（需手动安装）
- markdown: MD文件阅读
- Pillow: 图片处理

## 注意事项

如果提示缺少VC++运行时库，请下载安装：https://aka.ms/vs/16/release/vc_redist.x64.exe