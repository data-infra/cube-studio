#!/usr/bin/env bash

set -euo pipefail

echo "VC_WORKER_HOSTS=$VC_WORKER_HOSTS"
echo "VC_WORKER_NUM=$VC_WORKER_NUM"
echo "VC_TASK_INDEX=$VC_TASK_INDEX"

MASTER_ADDR="$(echo "$VC_WORKER_HOSTS" | cut -d',' -f1 | tr -d ' ')"
MASTER_PORT="${MASTER_PORT:-29500}"

# 每个Pod使用的GPU数量
NPROC_PER_NODE="${NPROC_PER_NODE:-1}"

apt-get update -y >/dev/null 2>&1 || true
apt-get install -y openssh-server >/dev/null 2>&1 || true

# 生成sshd主机密钥
ssh-keygen -A

mkdir -p /var/run/sshd
/usr/sbin/sshd

apt-get update -y >/dev/null 2>&1 || true
apt-get install -y openssh-server openssh-client net-tools netcat-traditional procps >/dev/null 2>&1 || true

ssh-keygen -A
mkdir -p /var/run/sshd
/usr/sbin/sshd

echo "[检查] sshd进程:"
ps -ef | grep '[s]shd' || true

echo "[检查] 端口22监听:"
netstat -lntp 2>/dev/null | grep ':22' || echo "端口22未监听"

WORKER1_HOST="$(echo "$VC_WORKER_HOSTS" | cut -d',' -f2)"
WORKER1_IP="$(getent hosts "$WORKER1_HOST" | awk '{print $1}' | head -n1 || true)"
echo "[检查] worker1主机=$WORKER1_HOST IP=$WORKER1_IP"

if [ "${VC_TASK_INDEX}" -eq 0 ]; then
  echo "[检查] 连接worker1:22"
  nc -vz -w 3 "$WORKER1_HOST" 22 || nc -vz -w 3 "$WORKER1_IP" 22 || echo "[失败] 无法连接worker1:22"
fi

# 准备训练代码
WORKDIR="/mnt/admin/pipeline/example/colossalai/test_train_colossalai"
mkdir -p "$WORKDIR"
cd "$WORKDIR"



# 生成hostfile
echo "$VC_WORKER_HOSTS" | tr "," "\n" | sed '/^\s*$/d' > ~/.myhostfile
echo "[主机列表]"
cat ~/.myhostfile
echo "[配置] MASTER_ADDR=$MASTER_ADDR MASTER_PORT=$MASTER_PORT NPROC_PER_NODE=$NPROC_PER_NODE"

# 只让rank0发起colossalai run（通过SSH拉起其他节点）
if [ "${VC_TASK_INDEX}" -eq 0 ]; then
  echo "[RANK0] 通过colossalai run启动..."

  # 直接使用SSH参数避免交互提示
  # 避免known_hosts验证卡住
  export COLOSSALAI_SSH_ARGS="${COLOSSALAI_SSH_ARGS:--o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR}"

  colossalai run \
    --nproc_per_node "$NPROC_PER_NODE" \
    --hostfile ~/.myhostfile \
    --master_addr "$MASTER_ADDR" \
    --master_port "$MASTER_PORT" \
    --ssh-port 22 \
    train_tiny_colossalai.py \
      --steps "${STEPS:-50}" \
      --batch_size "${BATCH_SIZE:-8}" \
      --lr "${LR:-1e-3}"

else
  echo "[WORKER ${VC_TASK_INDEX}] sshd已就绪，等待rank0启动..."
  tail -f /dev/null
fi