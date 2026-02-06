#!/bin/bash
set -euo pipefail
# 使用deepspeed任务模板跑
# 工作目录
cd /app 2>/dev/null || true

# 初始化环境变量
: "${VC_TASK_INDEX:=0}"            
: "${VC_WORKER_NUM:=1}"           
: "${VC_WORKER_HOSTS:=127.0.0.1}"  
: "${MASTER_PORT:=29500}"          
: "${GPU_NUM:=1}"                  

# MASTER_ADDR 取 host 列表第一个
MASTER_ADDR="$(echo "${VC_WORKER_HOSTS}" | tr -d ' ' | cut -d',' -f1)"

# 输出环境变量以便于验证调试
echo "VC_TASK_INDEX=${VC_TASK_INDEX}"
echo "VC_WORKER_NUM=${VC_WORKER_NUM}"
echo "VC_WORKER_HOSTS=${VC_WORKER_HOSTS}"
echo "MASTER_ADDR=${MASTER_ADDR}  MASTER_PORT=${MASTER_PORT}"
echo "GPU_NUM=${GPU_NUM}"

# DeepSpeed 引擎配置（Zero-3）
cat > ds_zero3.json <<'JSON'
{
  "train_batch_size": "auto",
  "train_micro_batch_size_per_gpu": "auto",
  "gradient_accumulation_steps": 8,

  "fp16": { "enabled": true },
  "bf16": { "enabled": false },

  "zero_optimization": {
    "stage": 3,
    "overlap_comm": true,
    "contiguous_gradients": true,
    "reduce_bucket_size": 500000000,
    "stage3_prefetch_bucket_size": 500000000,
    "stage3_param_persistence_threshold": 1000000,
    "stage3_gather_16bit_weights_on_model_save": true
  },

  "gradient_clipping": 1.0,
  "wall_clock_breakdown": false
}
JSON

# 启动ssh-server
# 若无ssh,pdsh 先安装ssh与deepspeed需要的库pdsh
apt update && apt install -y openssh-server pdsh
# 启动ssh
mkdir -p /var/run/sshd && /usr/sbin/sshd -D &

# 生成 hostfile
HOSTFILE=/tmp/hostfile
: > "${HOSTFILE}"
echo "${VC_WORKER_HOSTS}" | tr "," "\n" | sed "s/\$/ slots=${GPU_NUM}/" >> "${HOSTFILE}"


# 只保留这一个分支：rank0 启动；其它 rank 常驻等待 deepspeed 通信 
if [[ "${VC_TASK_INDEX}" -eq 0 ]]; then
  echo "[START] Launch DeepSpeed multinode job (launcher=pdsh)..."

  exec deepspeed \
    -H "${HOSTFILE}" \
    --launcher pdsh \
    --num_nodes "${VC_WORKER_NUM}" \
    --num_gpus "${GPU_NUM}" \
    --master_addr "${MASTER_ADDR}" \
    --master_port "${MASTER_PORT}" \
    src/train.py \
    --stage sft \
    --do_train \
    --model_name_or_path /mnt/admin/pipeline/example/deepseek/DeepSeek-R1-Distill-Qwen-7B \
    --dataset 'identity' \
    --template deepseekr1 \
    --finetuning_type lora \
    --lora_target all \
    --output_dir /mnt/admin/pipeline/example/deepseek/ppo/result/ \
    --per_device_train_batch_size 1 \
    --gradient_accumulation_steps 8 \
    --lr_scheduler_type cosine \
    --logging_steps 5 \
    --warmup_ratio 0.1 \
    --save_steps 1000 \
    --learning_rate 5e-5 \
    --num_train_epochs 5.0 \
    --max_samples 300 \
    --max_grad_norm 1.0 \
    --loraplus_lr_ratio 16.0 \
    --fp16 \
    --deepspeed ds_zero3.json
else
  echo "[INFO] Non-rank0 node, keeping alive and waiting..."
  sleep 365d
fi
