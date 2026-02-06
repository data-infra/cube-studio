#!/usr/bin/env bash
set -euo pipefail

# 训练超参
STEPS="${STEPS:-20}"
BATCH_SIZE="${BATCH_SIZE:-8}"
LR="${LR:-1e-3}"

WORKDIR="${WORKDIR:-/mnt/admin/pipeline/example/horovod_test}"
mkdir -p "$WORKDIR"
cd "$WORKDIR"

SSH_PORT="${SSH_PORT:-22}"
apt-get update -y >/dev/null 2>&1 || true
apt-get install -y openssh-server procps >/dev/null 2>&1 || true
ssh-keygen -A >/dev/null 2>&1 || true
mkdir -p /var/run/sshd
/usr/sbin/sshd -p "${SSH_PORT}" || true

echo "[信息]开始运行训练测试"

export NCCL_DEBUG="${NCCL_DEBUG:-INFO}"
export NCCL_IB_DISABLE="${NCCL_IB_DISABLE:-1}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"

python train_hvd_tiny.py --steps "${STEPS}" --batch_size "${BATCH_SIZE}" --lr "${LR}"
