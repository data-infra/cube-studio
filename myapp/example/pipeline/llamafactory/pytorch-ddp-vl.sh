#!/bin/bash
set -euo pipefail
# 使用pytorchjob任务模板跑
cd /app

# 初始化环境变量
: "${NCCL_DEBUG:=INFO}"                              
: "${GPU_NUM:=1}"                                    
: "${PYTHONUNBUFFERED:=0}"                           
: "${MASTER_PORT:=23456}"                            
: "${MASTER_ADDR:=127.0.0.1}"                        
: "${WORLD_SIZE:=1}"                                 
: "${RANK:=0}"                                       

export NCCL_DEBUG PYTHONUNBUFFERED MASTER_ADDR MASTER_PORT WORLD_SIZE RANK

# 根据环境变量计算启动参数
NUM_PROCESSES="${GPU_NUM}"                          
rem=$(( WORLD_SIZE % GPU_NUM ))
NNODES=$(( (WORLD_SIZE + GPU_NUM - 1) / GPU_NUM ))
NODE_RANK=$(( RANK / GPU_NUM ))

# 输出环境变量以供调试
echo "NCCL_DEBUG       = ${NCCL_DEBUG}"
echo "PYTHONUNBUFFERED = ${PYTHONUNBUFFERED}"
echo "MASTER_ADDR      = ${MASTER_ADDR}"
echo "MASTER_PORT      = ${MASTER_PORT}"
echo "GPU_NUM          = ${GPU_NUM}        -> nproc_per_node = ${NUM_PROCESSES}"
echo "WORLD_SIZE       = ${WORLD_SIZE}     -> nnodes         = ${NNODES}"
echo "RANK             = ${RANK}           -> node_rank      = ${NODE_RANK}"


cat > train.json <<'JSON'
{
  "stage": "sft",
  "do_train": true,

  "model_name_or_path": "/mnt/admin/pipeline/example/qwen-vl/qwen-vl-3b",

  "dataset": "identity",

  "template": "qwen2_vl",
  "finetuning_type": "lora",
  "lora_target": "all",
  "output_dir": "/mnt/admin/pipeline/example/qwen_vl/qwen_vl_ddp_lora",

  "per_device_train_batch_size": 1,
  "gradient_accumulation_steps": 8,
  "lr_scheduler_type": "cosine",
  "logging_steps": 5,
  "warmup_ratio": 0.1,
  "save_steps": 1000,
  "learning_rate": 5e-5,
  "num_train_epochs": 5.0,
  "max_samples": 300,
  "max_grad_norm": 1.0,

  "loraplus_lr_ratio": 16.0,
  "fp16": true
}
JSON

echo "===== Start torchrun (Pure DDP) ====="

exec torchrun \
  --nnodes "${NNODES}" \
  --node_rank "${NODE_RANK}" \
  --nproc_per_node "${NUM_PROCESSES}" \
  --master_addr "${MASTER_ADDR}" \
  --master_port "${MASTER_PORT}" \
  -m llamafactory.launcher train.json
