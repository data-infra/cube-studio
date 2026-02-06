# docker exec -it ccr.ccs.tencentyun.com/ascend/pytorch:2.1.0 bash
import os
import torch
import torch_npu
# 检查NPU是否可用
print(f"NPU available: {torch_npu.npu.is_available()}")

# 获取NPU设备数量
print(f"Number of NPUs: {torch_npu.npu.device_count()}")

# 获取当前NPU设备
print(f"Current NPU device: {torch_npu.npu.current_device()}")

import torch
import torch_npu

while True:
    # 创建NPU张量
    a = torch.randn(30000, 30000).npu()
    b = torch.randn(30000, 30000).npu()

    # 矩阵乘法
    c = torch.matmul(a, b)
    print(c)

    # 将结果移回CPU
    c_cpu = c.cpu()
    print(c_cpu)