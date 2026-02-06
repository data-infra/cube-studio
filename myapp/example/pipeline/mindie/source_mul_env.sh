
export RANK_TABLE_FILE=${MODEL_PATH}/ranktable-${KUBEFLOW_RUN_ID}.json
export RANKTABLEFILE=${MODEL_PATH}/ranktable-${KUBEFLOW_RUN_ID}.json
chmod 640 ${RANK_TABLE_FILE}
export MIES_CONTAINER_IP=$K8S_POD_IP

# 这两个数据在generate_rank_table.py中生成
export MASTER_IP=$(cat /master)
export WORLD_SIZE=$(cat /world_size)
