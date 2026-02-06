import datetime
import json
import subprocess
import sys
import re
import os
import time
import random

node_num = int(os.getenv('VC_WORKER_NUM',1))+int(os.getenv('VC_MASTER_NUM',0))
VC_TASK_INDEX = int(os.getenv('VC_TASK_INDEX','0'))
ROLE = os.getenv('ROLE','worker')
if ROLE == 'worker':
    VC_TASK_INDEX = VC_TASK_INDEX+int(os.getenv('VC_MASTER_NUM',0))
MODEL_PATH = os.getenv('MODEL_PATH','')
KUBEFLOW_RUN_ID = os.getenv('KUBEFLOW_RUN_ID','1')
rank_table_file = os.path.join(MODEL_PATH, f'ranktable-{KUBEFLOW_RUN_ID}.json')
RESOURCE_GPU = int(os.getenv('RESOURCE_GPU','8').split('(')[0])
K8S_HOST_IP = os.getenv('K8S_HOST_IP', '')
K8S_POD_IP = os.getenv('K8S_POD_IP', '')
# import pysnooper
# @pysnooper.snoop()
def get_npu_ips():
    """在本地执行命令获取NPU卡的IP地址"""
    npu_ips = {}
    for i in range(8):  # 假设每台机器有8张NPU卡
        try:
            # 执行本地命令
            result = subprocess.run(
                ['hccn_tool', '-i', str(i), '-ip', '-g'],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout

            # 使用正则表达式匹配IP地址
            ip_match = re.search(r'ipaddr+:(\d+\.\d+\.\d+\.\d+)', output)
            if ip_match:
                npu_ips[i]=ip_match.group(1)
            else:
                print(f"警告: 无法获取NPU {i}的IP地址")

        except subprocess.CalledProcessError as e:
            print(f"执行命令失败: {e}")

        except FileNotFoundError:
            print("错误: 未找到 hccn_tool 命令，请确保已安装并配置正确")

    if len(list(npu_ips.keys())) == RESOURCE_GPU:
        return npu_ips
    return None

# 查看当前master是否启动了
# @pysnooper.snoop()
def get_master_ready():
    if os.path.exists(rank_table_file):
        rank_table = json.load(open(rank_table_file))
        server_list = rank_table.get('server_list', [])
        for server in server_list:
            devices = server.get('device', [])
            for device in devices:
                rank_id = int(device.get('rank_id', -1))
                if rank_id == 0:
                    file = open('/master',mode='w')
                    file.write(server['server_id'])
                    file.close()
                    return True
    return False

# @pysnooper.snoop()
def create_rank_table():

    # 先检查master 是否已经弄好了，没弄好，就等着
    if ROLE.lower() == 'worker':
        while not get_master_ready():
            time.sleep(5)
            print('waiting master...')

    # 重启还是使用原有的
    if os.path.exists(rank_table_file):
        rank_table = json.load(open(rank_table_file))
    else:
        rank_table = {
            "server_count": str(node_num),
            "server_list": [],
            "status": "completed",
            "version": "1.0"
        }

    if ROLE.lower() == 'master':
        file = open('/master', mode='w')
        file.write(K8S_HOST_IP)
        file.close()

    current_rank = VC_TASK_INDEX*RESOURCE_GPU

    try:
        # 文件中加一个全局状态，master配置了就 master-starting，worker配置了就cluster-starting，全部启动完成就是running
        # master重启 不能清空配置
        # 先查询是否有有历史，一个是pod重启，一个是服务重启。

        # 获取NPU卡IP地址
        npu_ips = get_npu_ips()
        if not npu_ips:
            print(f"错误: 无法从本地服务器 获取NPU信息")
            exit(1)

        # 创建服务器条目
        server_entry = {
            "device": [],
            "server_id": K8S_HOST_IP,
            "container_ip": K8S_POD_IP,
            "host_nic_ip": "reserve",
            "node_rank": str(VC_TASK_INDEX)
        }

        # 这里device_id使用容器内从0开始的device_id
        for device_id, device_ip in enumerate(list(npu_ips.values())):
            device_entry = {
                "device_id": str(device_id),   # 这里要看传真实的，还是容器内的
                "device_ip": device_ip,
                "rank_id": str(current_rank)
            }
            current_rank += 1
            server_entry["device"].append(device_entry)

        # 这里如果是重启的话，并且如果跟之前的不一直的话，要全部重启，而不是只重启pod
        exist_server_list = rank_table.get('server_list', [])
        exist_node_rank={}
        for server in exist_server_list:
            node_rank = server.get('node_rank', -1)
            if node_rank == str(VC_TASK_INDEX):
                exist_node_rank = server

        # 判断exist_node_rank 和新生成是否一样
        if not exist_node_rank:
            rank_table["server_list"].append(server_entry)
        else:
            if exist_node_rank!=server_entry:
                print('发现pod重启漂移到其他节点，和已存在ranktable存在不一致，请清理推理服务，并重新部署')
                exit(1)

    except Exception as e:
        print(f"处理服务器 {K8S_HOST_IP} 时出错: {str(e)}")
        exit(1)

    json.dump(rank_table, open(rank_table_file, 'w'),indent=4,ensure_ascii=False)
    while True:
        time.sleep(5)
        server_list = json.load(open(rank_table_file)).get('server_list',[])
        if len(server_list) == node_num:
            print(f"rank table {rank_table_file} ok")
            file = open('/world_size', 'w')
            file.write(str(node_num*RESOURCE_GPU))
            file.close()
            return
        print('waiting all nodes...')



if __name__ == "__main__":
    create_rank_table()
