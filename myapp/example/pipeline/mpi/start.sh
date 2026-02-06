#!/usr/bin/env bash
set -euo pipefail

SCRIPT_LOCAL="tensorflow2_mnist.py"

# 优先使用MPIJob提供的hostfile；如果用户设置了HOSTFILE则使用用户设置
HOSTFILE="${HOSTFILE:-${OMPI_MCA_orte_default_hostfile:-/etc/mpi/hostfile}}"

# 对于MPIJob，不进行ssh检查
CHECK_SSH="${CHECK_SSH:-0}"

# 每个worker(节点)的进程数，默认为1
PPR="${PPR:-1}"

# 总进程数，如果未设置则使用WORLD_SIZE，否则计算hostfile行数
if [[ -z "${NP:-}" ]]; then
  if [[ -n "${WORLD_SIZE:-}" ]]; then
    NP="${WORLD_SIZE}"
  else
    NP="$(awk 'BEGIN{n=0} /^[[:space:]]*#/ {next} NF==0 {next} {n++} END{print n}' "$HOSTFILE")"
  fi
fi

echo "[信息] OMPI_MCA_plm_rsh_agent: ${OMPI_MCA_plm_rsh_agent:-}"
echo "[信息] OMPI_MCA_orte_default_hostfile: ${OMPI_MCA_orte_default_hostfile:-}"
echo "[信息] HOSTFILE=$HOSTFILE"
echo "[信息] WORLD_SIZE=${WORLD_SIZE:-} RANK=${RANK:-} (mpirun主机发现不使用这些变量)"
echo "[信息] PPR=$PPR  NP=$NP"

if [[ ! -f "$HOSTFILE" ]]; then
  echo "[错误] hostfile未找到: $HOSTFILE"
  exit 1
fi

echo "[信息] ----- hostfile内容 -----"
cat "$HOSTFILE" || true
echo "[信息] ----------------------------"


command -v mpirun >/dev/null 2>&1 || { echo "[错误] mpirun未找到"; exit 1; }
command -v python >/dev/null 2>&1 || { echo "[错误] python未找到"; exit 1; }

# 容器中允许以root运行
ALLOW_ROOT_FLAG=""
if [[ "$(id -u)" == "0" ]]; then
  ALLOW_ROOT_FLAG="--allow-run-as-root"
fi

# 传递有用的环境变量
export NCCL_DEBUG="${NCCL_DEBUG:-INFO}"
export NCCL_SOCKET_IFNAME="${NCCL_SOCKET_IFNAME:-eth0}"
export HOROVOD_LOG_LEVEL="${HOROVOD_LOG_LEVEL:-INFO}"
# export HOROVOD_GPU_ALLREDUCE=NCCL   # 仅在horovod支持NCCL时启用

echo "[信息] 启动mpirun..."
set -x
mpirun -np "$NP" \
  --hostfile "$HOSTFILE" \
  $ALLOW_ROOT_FLAG \
  -bind-to none \
  -map-by "ppr:${PPR}:node" \
  -x LD_LIBRARY_PATH -x PATH -x PYTHONPATH \
  -x NCCL_DEBUG -x NCCL_SOCKET_IFNAME \
  -x HOROVOD_LOG_LEVEL -x HOROVOD_GPU_ALLREDUCE \
  -mca pml ob1 -mca btl ^openib \
  python "$SCRIPT_LOCAL"
set +x

echo "[信息] 完成."
