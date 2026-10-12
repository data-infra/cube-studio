#!/usr/bin/env bash
set -ex

hubhost=ccr.ccs.tencentyun.com/cube-studio
# Ubuntu 22.04 支持现有 Python 3.9 PPA，官方 CUDA 12.6 镜像使用 cuDNN 9。
base_image=nvidia/cuda:12.6.3-cudnn-devel-ubuntu22.04
cuda_image=$hubhost/ubuntu-gpu:cuda12.6.3-cudnn9
python_image=$hubhost/ubuntu-gpu:cuda12.6.3-cudnn9-python3.9

# 使用当前构建器，环境需支持多架构输出及两种架构的执行（原生节点或模拟器）。
# 先推送 CUDA 层的多架构标签，供下一步按目标架构拉取基础镜像。
docker buildx build --platform linux/amd64,linux/arm64 \
    --network=host --allow=network.host \
    -t "$cuda_image" \
    --build-arg FROM_IMAGES="$base_image" \
    -f cuda/Dockerfile --push .

# Buildx 自动发布包含两种架构的统一标签，无需手动创建 manifest。
docker buildx build --platform linux/amd64,linux/arm64 \
    --network=host --allow=network.host \
    -t "$python_image" \
    --build-arg FROM_IMAGES="$cuda_image" \
    --build-arg PYTHON_VERSION=python3.9 \
    -f cuda/python/Dockerfile --push .
