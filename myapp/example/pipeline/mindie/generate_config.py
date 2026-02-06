import json
import os,re

RESOURCE_GPU = int(os.getenv('RESOURCE_GPU','8').split('(')[0])
node_num = int(os.getenv('VC_WORKER_NUM',1))+int(os.getenv('VC_MASTER_NUM',0))
config_path = '/usr/local/Ascend/mindie/latest/mindie-service/conf/config.json'
def create_config():
    config = json.load(open(config_path))
    config['ServerConfig']['ipAddress']='0.0.0.0'
    config['ServerConfig']['managementIpAddress']='0.0.0.0'
    config['ServerConfig']['allowAllZeroIpListening']=True
    config['ServerConfig']['httpsEnabled']=False
    config['ServerConfig']['interCommTLSEnabled']=False
    config['BackendConfig']['npuDeviceIds']=[list(range(RESOURCE_GPU))]
    config['BackendConfig']['interNodeTLSEnabled'] = False

    if node_num>1:
        config['BackendConfig']['multiNodesInferEnabled']=True
    config['BackendConfig']['ModelDeployConfig']['ModelConfig'][0]['modelName'] = os.getenv('MODEL_NAME','mindie')
    config['BackendConfig']['ModelDeployConfig']['ModelConfig'][0]['modelWeightPath'] = os.getenv('MODEL_PATH','')
    config['BackendConfig']['ModelDeployConfig']['ModelConfig'][0]['worldSize'] = RESOURCE_GPU

    json.dump(config,open(config_path,mode='w'),indent=4,ensure_ascii=True)

if __name__ == "__main__":
    create_config()
