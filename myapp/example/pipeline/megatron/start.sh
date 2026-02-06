#!/usr/bin/env bash

# Megatron Core的基础冒烟测试示例 镜像使用:nvcr.io/nvidia/pytorch:24.08-py3
# 示例将会运行Megatron官方冒烟测试示例进行测试,包含能启动,能组网,能建模,能训练一步,能做基本 I/O/状态

set -euo pipefail

LAUNCH_ROLE="${LAUNCH_ROLE:-worker}"
ROLE="${VC_TASK_ROLE:-worker}"

if [[ "$ROLE" != "$LAUNCH_ROLE" ]]; then
  echo "角色=$ROLE (不是启动角色: $LAUNCH_ROLE), 退出."
  exit 0
fi

ROLE_UP="$(echo "$ROLE" | tr '[:lower:]' '[:upper:]')"
HOSTS="$(printenv "VC_${ROLE_UP}_HOSTS" 2>/dev/null || true)"
NNODES="$(printenv "VC_${ROLE_UP}_NUM" 2>/dev/null || echo 1)"
NODE_RANK="${VC_TASK_INDEX:-0}"

if [[ -n "${GPU_NUM:-}" && "${GPU_NUM:-0}" -gt 0 ]]; then
  NPROC_PER_NODE="$GPU_NUM"
else
  if command -v nvidia-smi >/dev/null 2>&1; then
    NPROC_PER_NODE="$(nvidia-smi -L | wc -l | tr -d ' ')"
  else
    NPROC_PER_NODE=1
  fi
fi

MASTER_ADDR="${MASTER_ADDR:-$(echo "$HOSTS" | tr ',' ' ' | awk '{print $1}')}"
MASTER_ADDR="${MASTER_ADDR:-127.0.0.1}"
MASTER_PORT="${MASTER_PORT:-29500}"

echo "ROLE=$ROLE"
echo "HOSTS=$HOSTS"
echo "NNODES=$NNODES"
echo "NODE_RANK=$NODE_RANK"
echo "NPROC_PER_NODE=$NPROC_PER_NODE"
echo "MASTER_ADDR=$MASTER_ADDR"
echo "MASTER_PORT=$MASTER_PORT"

export NCCL_DEBUG="${NCCL_DEBUG:-INFO}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-1}"

# ============================
# 克隆Git仓库
# ============================
MEGATRON_GIT_URL="${MEGATRON_GIT_URL:-https://github.com/NVIDIA/Megatron-LM.git}"
MEGATRON_DIR="${MEGATRON_DIR:-$PWD/Megatron-LM}"
MEGATRON_GIT_REF="${MEGATRON_GIT_REF:-main}"
MEGATRON_UPDATE="${MEGATRON_UPDATE:-0}"
LOCK_DIR="${MEGATRON_DIR}.lockdir"

wait_for_repo() {
  local i
  for i in $(seq 1 600); do
    if [[ -d "$MEGATRON_DIR/.git" ]]; then return 0; fi
    sleep 1
  done
  echo "错误: 等待仓库超时: $MEGATRON_DIR" >&2
  exit 1
}

if [[ ! -d "$MEGATRON_DIR/.git" ]]; then
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    echo "[锁] 已获取: $LOCK_DIR"
    cleanup_lock() { rmdir "$LOCK_DIR" 2>/dev/null || true; }
    trap cleanup_lock EXIT

    if [[ ! -d "$MEGATRON_DIR/.git" ]]; then
      echo "[克隆] git clone $MEGATRON_GIT_URL -> $MEGATRON_DIR"
      git clone "$MEGATRON_GIT_URL" "$MEGATRON_DIR"
    fi

    git -C "$MEGATRON_DIR" checkout "$MEGATRON_GIT_REF" || true
    if [[ "$MEGATRON_UPDATE" == "1" ]]; then
      git -C "$MEGATRON_DIR" fetch --all --tags
      git -C "$MEGATRON_DIR" checkout "$MEGATRON_GIT_REF" || true
      git -C "$MEGATRON_DIR" pull --ff-only || true
    fi

    cleanup_lock
    trap - EXIT
    echo "[锁] 已释放: $LOCK_DIR"
  else
    echo "[锁] 忙碌中, 等待仓库..."
    while [[ -d "$LOCK_DIR" ]]; do sleep 1; done
    wait_for_repo
  fi
else
  echo "[克隆] 已存在: $MEGATRON_DIR"
fi

cd "$MEGATRON_DIR"
export PYTHONPATH="$MEGATRON_DIR:${PYTHONPATH:-}"

DEPS_ROOT="${DEPS_ROOT:-$MEGATRON_DIR/.deps}"
DEPS_DIR="${DEPS_ROOT}/node${NODE_RANK}"
mkdir -p "$DEPS_DIR"

echo "[依赖] python=$(which python)"
python -V

echo "[依赖] 安装 numpy==1.26.4 到 $DEPS_DIR"
python -m pip install -U --no-cache-dir --target "$DEPS_DIR" "numpy==1.26.4" -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# 确保优先使用这个numpy
export PYTHONPATH="$DEPS_DIR:$MEGATRON_DIR:${PYTHONPATH:-}"

echo "[依赖] 验证numpy导入..."
python - <<'PY'
import numpy as np
print("numpy版本:", np.__version__)
print("numpy文件:", np.__file__)
from numpy.dtypes import UInt32DType
print("numpy.dtypes 正常")
PY


EXAMPLE_ARGS="${EXAMPLE_ARGS:-}"

echo "[运行] torchrun ... examples/run_simple_mcore_train_loop.py ${EXAMPLE_ARGS}"

exec torchrun \
  --nnodes="$NNODES" \
  --node_rank="$NODE_RANK" \
  --nproc_per_node="$NPROC_PER_NODE" \
  --master_addr="$MASTER_ADDR" \
  --master_port="$MASTER_PORT" \
  examples/run_simple_mcore_train_loop.py "$EXAMPLE_ARGS"

echo "测试完毕, 使用torchrun启动MEGATRON分布式运行完成."