source /usr/local/Ascend/mindie/set_env.sh
source /usr/local/Ascend/ascend-toolkit/set_env.sh
source /usr/local/Ascend/nnal/atb/set_env.sh
source /usr/local/Ascend/atb-models/set_env.sh
export ATB_LLM_BENCHMARK_ENABLE=1
export ATB_LLM_ENABLE_AUTO_TRANSPOSE=0

export HCCL_CONNECT_TIMEOUT=7200
export HCCL_EXEC_TIMEOUT=0
export OMP_NUM_THREADS=1

export MINDIE_LOG_TO_STDOUT=1
export MINDIE_LLM_LOG_TO_STDOUT=1
export PYTORCH_NPU_ALLOC_CONF=expandable_segments:True
export ATB_WORKSPACE_MEM_ALLOC_ALG_TYPE=3
export ATB_WORKSPACE_MEM_ALLOC_GLOBAL=1

export NPU_MEMORY_FRACTION=0.9
export HCCL_DETERMINISTIC=false
export HCCL_OP_EXPANSION_MODE="AIV"

export ATB_LLM_HCCL_ENABLE=1
export ATB_LLM_COMM_BACKEND="hccl"
export HCCL_CONNECT_TIMEOUT=7200


chmod 640 /usr/local/Ascend/mindie/latest/mindie-service/conf/config.json
chmod -R 640 $MODEL_PATH
