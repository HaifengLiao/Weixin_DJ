import torch
print(torch.version.cuda)  # 应输出 "11.6" 或 "11.8"
print(torch.cuda.is_available())  # 应输出 True（若使用 GPU 版本）
