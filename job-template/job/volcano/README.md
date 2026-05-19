# Volcano 任务模板说明（分布式计算）

本模板通过创建 **Volcano Job** CRD（`batch.volcano.sh/v1alpha1`），帮助你在平台上发起**多副本分布式计算任务**。所有 Worker Pod 使用相同镜像与命令，由 Volcano 调度器统一调度，并通过环境变量区分当前副本序号，适合数据并行、批处理等场景。

---

## 1. 任务模板功能简介与使用场景

### 1.1 功能简介

- **多副本并行**：按你指定的 Worker 数量（`--num_worker`）创建一组 Pod，每个 Pod 执行同一条命令（`--command`），工作目录为 `--working_dir`，镜像可为模板默认或通过 `--image` 指定。
- **Volcano 调度**：使用 Volcano 调度器（`schedulerName: volcano`）和默认队列（`queue: default`），配合 `minAvailable` 保证所需副本数就绪后再运行，适合批量、 gang 调度需求。
- **日志与状态**：Launcher 使用 `stern` 实时汇聚所有 Worker Pod 的日志；后台线程轮询 Volcano Job 状态，在 `Completed` / `Failed` / `Aborted` / `Terminated` 时结束任务并以对应退出码退出。

### 1.2 使用场景

- **数据并行**：同一份代码在多机上跑不同分片数据（如按 `VC_TASK_INDEX` 分片），适合大规模数据处理、ETL、离线训练等。
- **批处理 / 多机任务**：需要多台机器同时执行相同程序、通过 rank/index 区分逻辑的场景。
- **与现有 Volcano 集群集成**：集群已部署 Volcano 时，可直接复用其队列与调度能力，无需再引入其他分布式框架。

---

## 2. 任务模板设计思路

### 2.1 整体流程

- **Launcher 容器**：平台先拉起本模板的 Launcher 镜像，执行 `python3 launcher.py`，并传入界面配置的参数：`--working_dir`、`--command`、`--num_worker`、`--image`。
- **创建 Volcano Job**：Launcher 根据环境变量（如 `KFJ_TASK_RESOURCE_CPU/MEMORY/GPU`、`KFJ_TASK_VOLUME_MOUNT`、`KFJ_NAMESPACE`、节点选择等）与上述参数，组装成 Volcano 的 `Job` 资源（`batch.volcano.sh/v1alpha1`），提交到当前任务命名空间。
- **运行与监控**：Volcano 创建名为 `worker` 的 Task，副本数等于 `--num_worker`，每个 Pod 均以 `bash -c` 执行 `--command`。Launcher 后台线程轮询 Job 状态；主线程通过 `stern` 跟踪 Pod 日志（每约 1 小时会重启 stern 以规避长时间跟踪限制），直到 Job 结束。
- **退出与结果**：当 Job 状态为 `Completed` 时 Launcher 退出码 0，否则（如 `Failed` / `Aborted` / `Terminated`）退出码 1，平台据此判断任务成功或失败。

### 2.2 资源与调度

- **资源**：每个 Pod 的 CPU、内存来自 `KFJ_TASK_RESOURCE_CPU`、`KFJ_TASK_RESOURCE_MEMORY`；若配置了 GPU（`KFJ_TASK_RESOURCE_GPU`、`GPU_RESOURCE_NAME`），会为容器设置 requests/limits，并可根据 `gpu_type` 做节点亲和；支持 RDMA（`KFJ_TASK_RESOURCE_RDMA`）；另有 `DEFAULT_POD_RESOURCES` 可扩展 requests/limits。
- **调度**：使用 `KFJ_TASK_NODE_SELECTOR` 做节点选择；若识别到 GPU 类型则写入节点亲和；通过 Pod 反亲和（`preferredDuringSchedulingIgnoredDuringExecution`）尽量将同一 Job 的 Pod 分散到不同节点（`topologyKey: kubernetes.io/hostname`）。
- **挂载与镜像**：使用 `KFJ_TASK_VOLUME_MOUNT` 解析出的 volumes / volumeMounts 挂载到所有 Pod；镜像拉取使用 `HUBSECRET`（环境变量，逗号分隔的 secret 名）。

### 2.3 Volcano Job 结构要点

- **Task**：仅一个 Task 类型 `worker`，`replicas` = `num_workers`，所有 Pod 共用同一 `template`（镜像、工作目录、命令、资源、挂载一致）。
- **调度与队列**：`schedulerName: "volcano"`，`queue: "default"`，`minAvailable: num_workers`；`cleanPodPolicy: "None"`。
- **插件**：启用 `env`、`svc`、`ssh`，便于 Pod 间通过服务发现与 SSH 协作（若需要）。
- **副本标识**：Volcano 会为各 Pod 注入诸如 `VC_WORKER_NUM`、`VC_TASK_INDEX` 等环境变量（具体以集群 Volcano 版本为准），用户代码可据此做分片或协同。

---

## 3. 在任务模板中注册配置

在 Cube Studio 中：**训练 → 任务模板 → 添加**，按下面方式配置即可将本模板注册到平台。

### 3.1 基本信息

| 配置项 | 说明 | 建议值 |
|--------|------|--------|
| 模板名称 | 英文名，用于编排界面展示 | `volcano` 或 `volcanojob` |
| 描述 | 中文说明 | Volcano 分布式计算 |
| 模板版本 | 仅 Release 会在编排界面展示 | Release |
| 目录 | 覆盖镜像工作目录（可选） | 可不填 |
| 启动命令 | 覆盖镜像入口，必须能调起 launcher | `python3 launcher.py` |

### 3.2 镜像与仓库

- **模板镜像**：Launcher 所在镜像，例如  
  `ccr.ccs.tencentyun.com/cube-studio/volcano:20230601`
- 若使用私有仓库，需先在 **训练 → 仓库** 中配置账号，并在 **训练 → 镜像** 中添加该镜像。

### 3.3 环境变量

本模板依赖以下环境变量（由平台或任务配置注入），建议在模板中配置示例值：

```bash
NO_RESOURCE_CHECK=true
TASK_RESOURCE_CPU=2
TASK_RESOURCE_MEMORY=4G
TASK_RESOURCE_GPU=0
TASK_RESOURCE_RDMA=0
```

（实际每 Pod 的 CPU/内存/GPU 会由平台和任务配置一起生效；Launcher 会读取 `KFJ_TASK_*`、`GPU_RESOURCE_NAME` 等组装 Volcano Job。）

### 3.4 挂载目录

按需填写。例如不强制挂载可留空；若需统一挂载用户工作目录，可使用平台提供的 PVC 或 hostpath 规则（如 `kubeflow-user-workspace(pvc):/mnt` 等），与平台约定一致。

### 3.5 K8s 账号

填写：**kubeflow-pipeline**（或你部署 Volcano Job 时使用的 ServiceAccount）。  
Launcher 会创建/删除 Volcano Job CRD 及查看 Pod 事件，需要具备对应命名空间下 CRD 与 Pod 的权限。

### 3.6 启动参数（args）

用于在编排界面展示和传入 launcher 的 JSON 需与 `launcher.py` 的 `arg_parser` 对应，建议使用以下结构（键名需与命令行参数一致，如 `--working_dir`、`--command`、`--num_worker`、`--image`）：

```json
{
  "shell": {
    "--working_dir": {
      "type": "str",
      "item_type": "str",
      "label": "启动目录",
      "require": 1,
      "choice": [],
      "range": "",
      "default": "/mnt/admin",
      "placeholder": "",
      "describe": "运行 job 的工作目录",
      "editable": 1
    },
    "--command": {
      "type": "str",
      "item_type": "str",
      "label": "启动命令",
      "require": 1,
      "choice": [],
      "range": "",
      "default": "python3 mnist.py",
      "placeholder": "",
      "describe": "运行 job 的命令，由 bash -c 执行",
      "editable": 1
    },
    "--num_worker": {
      "type": "str",
      "item_type": "str",
      "label": "Worker 数量",
      "require": 1,
      "choice": [],
      "range": "",
      "default": "3",
      "placeholder": "",
      "describe": "分布式 Worker 的数量（Pod 副本数）",
      "editable": 1
    },
    "--image": {
      "type": "str",
      "item_type": "str",
      "label": "Worker 镜像",
      "require": 0,
      "choice": [],
      "range": "",
      "default": "ccr.ccs.tencentyun.com/cube-studio/ubuntu-gpu:cuda11.8.0-cudnn8-python3.9",
      "placeholder": "",
      "describe": "Worker 镜像，直接运行你代码的环境镜像。不填则使用模板默认镜像。<a href='https://github.com/data-infra/cube-studio/tree/main/images'>基础镜像</a>",
      "editable": 1
    }
  }
}
```

## 4. 用户如何使用这个任务模板

### 4.1 在流水线中选用模板

1. 在 **训练 → 流水线** 中创建或编辑流水线，添加任务节点。
2. 在任务的 **任务模板** 中选择已注册的 Volcano 模板（如 `volcano`）。
3. 填写该任务节点的 **启动目录**、**启动命令**、**Worker 数量**、**Worker 镜像**（或使用默认），以及任务级别的资源、挂载等。

平台会把这些参数以 `--working_dir`、`--command`、`--num_worker`、`--image` 等形式传给 Launcher，Launcher 再据此创建 Volcano Job。

### 4.2 用户代码约定（分布式逻辑）

- 保留单机代码结构，在此基础上通过**集群信息**区分当前是第几个 Worker、共多少个 Worker。
- Volcano 会为每个 Pod 注入环境变量（具体名称以集群 Volcano 版本为准），常见例如：
  - `VC_WORKER_NUM`：Worker 总数  
  - `VC_TASK_INDEX`：当前 Worker 的序号（从 0 开始）
- 在代码中读取上述变量，对数据或任务做**分片**：例如只处理 `index % WORLD_SIZE == RANK` 的数据，实现数据并行。

### 4.3 用户代码示例

下面示例：根据 `VC_WORKER_NUM` 和 `VC_TASK_INDEX` 将 300 个任务均匀分到多个 Worker，每个 Worker 内部可用多进程/线程池加速。

```python
import time, datetime, json, requests, io, os
from multiprocessing import Pool
from functools import partial
import os, random, sys

# 总 Worker 数目与当前 Worker 序号（由 Volcano 注入，未设置时默认为 1 和 0）
WORLD_SIZE = int(os.getenv('VC_WORKER_NUM', '1'))
RANK = int(os.getenv("VC_TASK_INDEX", '0'))

print('WORLD_SIZE=%s RANK=%s' % (WORLD_SIZE, RANK), flush=True)


def task(key):
    print(datetime.datetime.now(), 'worker:', RANK, ', task:', key, flush=True)
    time.sleep(1)


if __name__ == '__main__':
    # 所有要处理的数据
    input = range(300)
    # 当前 Worker 只处理 index % WORLD_SIZE == RANK 的数据
    local_task = [index for index in input if index % WORLD_SIZE == RANK]

    # 每个 Worker 内部可用多进程/线程池
    pool = Pool(10)
    pool.map(partial(task), local_task)
    pool.close()
    pool.join()
```
