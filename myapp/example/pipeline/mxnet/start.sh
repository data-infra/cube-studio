#!/usr/bin/env bash
set -e

echo "MX_CONFIG: ${MX_CONFIG:-}"
echo "DMLC_PS_ROOT_PORT: ${DMLC_PS_ROOT_PORT:-}"
echo "DMLC_PS_ROOT_URI: ${DMLC_PS_ROOT_URI:-}"
echo "DMLC_NUM_SERVER: ${DMLC_NUM_SERVER:-}"
echo "DMLC_NUM_WORKER: ${DMLC_NUM_WORKER:-}"
echo "DMLC_ROLE: ${DMLC_ROLE:-}"
echo "DMLC_USE_KUBERNETES: ${DMLC_USE_KUBERNETES:-}"

ROLE="${DMLC_ROLE:-worker}"

# 工作目录（MXNet 官方 image-classification 示例目录）
WORK_DIR="/incubator-mxnet/example/image-classification"
SCRIPT_NAME="train_mnist.py"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cp -f "./${SCRIPT_NAME}" "${WORK_DIR}/${SCRIPT_NAME}"
cd "${WORK_DIR}"

# 训练参数（可通过环境变量覆盖）
PYTHON_BIN="${PYTHON_BIN:-python}"
NETWORK="${NETWORK:-mlp}"
NUM_EPOCHS="${NUM_EPOCHS:-10}"
NUM_LAYERS="${NUM_LAYERS:-2}"
BATCH_SIZE="${BATCH_SIZE:-64}"
LR="${LR:-0.05}"
DATA_DIR="${DATA_DIR:-/tmp/mnist-data}"

# 判断是否有 GPU
HAS_GPU=0
if command -v nvidia-smi >/dev/null 2>&1; then
  if nvidia-smi -L >/dev/null 2>&1; then
    HAS_GPU=1
  fi
fi

# kvstore：分布式优先 dist_*；单机优先 device/local
if [[ -z "${KV_STORE:-}" ]]; then
  if [[ -n "${DMLC_ROLE:-}" ]]; then
    # 分布式
    if [[ "${HAS_GPU}" -eq 1 ]]; then
      KV_STORE="dist_device_sync"
    else
      KV_STORE="dist_sync"
    fi
  else
    # 单机
    if [[ "${HAS_GPU}" -eq 1 ]]; then
      KV_STORE="device"
    else
      KV_STORE="local"
    fi
  fi
else
  KV_STORE="${KV_STORE}"
fi

# GPU 参数（只给 worker 传；server/scheduler 不需要）
GPU_ARG=()
if [[ "${ROLE}" == "worker" && "${HAS_GPU}" -eq 1 ]]; then
  # 优先用 GPUS 环境变量，否则默认用 0
  if [[ -n "${GPUS:-}" ]]; then
    GPU_ARG=(--gpus "${GPUS}")
  else
    GPU_ARG=(--gpus "0")
  fi
fi

CMD=(
  "${PYTHON_BIN}" "${SCRIPT_NAME}"
  --network "${NETWORK}"
  --num-epochs "${NUM_EPOCHS}"
  --num-layers "${NUM_LAYERS}"
  --batch-size "${BATCH_SIZE}"
  --lr "${LR}"
  --kv-store "${KV_STORE}"
  --data-dir "${DATA_DIR}"
)

echo "=================================================="
echo "ROLE=${ROLE} | KV_STORE=${KV_STORE} | HAS_GPU=${HAS_GPU}"
echo "CMD: ${CMD[*]} ${GPU_ARG[*]}"
echo "=================================================="

case "${ROLE}" in
  scheduler|server)
    # scheduler/server 也必须跑同一条 python 命令，MXNet 在 import 时会启动对应进程并阻塞
    exec "${CMD[@]}"
    ;;
  worker)
    exec "${CMD[@]}" "${GPU_ARG[@]}"
    ;;
  *)
    echo "DMLC_ROLE未设置或值无效: '${ROLE}'"
    exit 1
    ;;
esac
