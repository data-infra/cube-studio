# TFJob 任务模板说明（TensorFlow 分布式训练）

本模板通过创建 Kubeflow **TFJob** CRD，帮助你在平台上发起 **TensorFlow 分布式训练**（多 Worker 模式），并自动跟踪日志与任务状态。

---

## 1. 任务模板设计思路

### 1.1 整体流程

- **Launcher 容器**：平台先拉起本模板的 Launcher 镜像，执行 `python3 launcher.py`，并传入你在界面填写的参数（`--image`、`--working_dir`、`--command`、`--num_worker`）。
- **创建 TFJob**：Launcher 根据环境变量（如 CPU/内存/GPU、挂载、命名空间等）和上述参数，组装成 Kubeflow 的 `TFJob` 资源（`kubeflow.org/v1`），并提交到当前任务的命名空间。
- **运行与监控**：TFJob 会创建若干 Worker Pod。Launcher 使用 `stern` 实时汇聚这些 Pod 的日志到当前任务日志；同时后台线程轮询 TFJob 状态，直到 `Succeeded` 或 `Failed`。
- **退出与结果**：当 TFJob 结束时，Launcher 退出。若状态为 `Succeeded` 则退出码 0，否则退出码 1，平台据此判断任务成功或失败。

### 1.2 角色与副本

- **Worker**：执行你指定的 `--command`（由 `bash -c` 执行），工作目录为 `--working_dir`。副本数由 `--num_worker` 决定。
- 本模板仅使用 **Worker** 角色（无 PS/Chief），适用于 TensorFlow 2.x 的 `tf.distribute` 等多 Worker 分布式场景。

### 1.3 资源与调度

- **资源**：每个 Pod 的 CPU、内存来自平台下发的 `KFJ_TASK_RESOURCE_CPU`、`KFJ_TASK_RESOURCE_MEMORY`；若配置了 GPU，则通过 `KFJ_TASK_RESOURCE_GPU` 和 `GPU_RESOURCE_NAME` 为容器申请对应数量的 GPU；无 GPU 时会设置 `NVIDIA_VISIBLE_DEVICES=none` 禁用 GPU。
- **调度**：使用 `KFJ_TASK_NODE_SELECTOR` 做节点选择；若有 GPU 类型信息则写入节点亲和；通过 Pod 反亲和尽量将同一 TFJob 的 Pod 分散到不同节点。
- **挂载**：使用 `KFJ_TASK_VOLUME_MOUNT` 解析出的 volumes / volumeMounts 挂载到所有 Pod，保证训练代码与数据在 `--working_dir` 下可用。

### 1.4 策略与约束

- **cleanPodPolicy**：`None`，任务结束不自动删除 Pod，便于排查。
- **backoffLimit**：等于 `num_worker`，控制重试行为。
- **容器名**：Worker 容器名称固定为 `tensorflow`（TFJob 规范要求）。
- **日志**：使用 `stern` 跟踪 TFJob 下所有 Pod 的日志，便于用户直接看到训练输出。

---

## 2. 在任务模板中注册配置

在 CubeStudio 中：**训练 → 任务模板 → 添加**，按下面方式配置即可将本模板注册到平台。

### 2.1 基本信息

| 配置项 | 说明 | 建议值 |
|--------|------|--------|
| 模板名称 | 英文名，用于编排界面展示 | `tfjob` |
| 描述 | 中文说明 | TensorFlow 分布式训练 |
| 模板版本 | 仅 Release 会在编排界面展示 | Release |
| 目录 | 覆盖镜像工作目录（可选） | 可不填 |
| 启动命令 | 覆盖镜像入口，必须能调起 launcher | `python3 launcher.py` |

### 2.2 镜像与仓库

- **模板镜像**：Launcher 所在镜像，例如  
  `ccr.ccs.tencentyun.com/cube-studio/tf:20230801`
- 若使用私有仓库，需先在 **训练 → 仓库** 中配置账号，并在 **训练 → 镜像** 中添加该镜像。

### 2.3 环境变量

本模板需要固定资源由环境变量控制，建议配置为：

```bash
NO_RESOURCE_CHECK=true
TASK_RESOURCE_CPU=2
TASK_RESOURCE_MEMORY=4G
TASK_RESOURCE_GPU=0
```

（实际每 Pod 的 CPU/内存/GPU 会由平台和 `--image` 对应任务配置一起生效；Launcher 会读取 `KFJ_TASK_*` 等环境变量组装 TFJob。）

### 2.4 挂载目录

按需填写。例如不强制挂载可留空；若需统一挂载用户工作目录，可使用平台提供的 PVC 或 hostpath 规则（如 `kubeflow-user-workspace(pvc):/mnt` 等，与平台约定一致）。

### 2.5 K8s 账号

填写：**kubeflow-pipeline**（或你部署 TFJob 时使用的 ServiceAccount）。  
因为 Launcher 会创建 TFJob 及下属 Pod，需要具备对应命名空间下创建 CRD 的权限。

### 2.6 启动参数（args）

用于在编排界面展示和传入 launcher 的 JSON 结构如下（与 `launcher.py` 的 `arg_parser` 对应）：

```json
{
  "参数": {
    "--image": {
      "type": "str",
      "item_type": "str",
      "label": "worker镜像",
      "require": 1,
      "choice": [],
      "range": "",
      "default": "ccr.ccs.tencentyun.com/cube-studio/ubuntu-gpu:cuda11.8.0-cudnn8-python3.9",
      "placeholder": "",
      "describe": "worker镜像，直接运行你代码的环境镜像 <a href='https://github.com/data-infra/cube-studio/tree/main/images'>基础镜像</a>",
      "editable": 1
    },
    "--working_dir": {
      "type": "str",
      "item_type": "str",
      "label": "启动目录",
      "require": 1,
      "choice": [],
      "range": "",
      "default": "/mnt/xxx/tfjob/",
      "placeholder": "",
      "describe": "命令的启动目录",
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
      "placeholder": "启动命令，例如 python3 xxx.py",
      "describe": "启动命令，例如 python3 xxx.py",
      "editable": 1
    },
    "--num_worker": {
      "type": "str",
      "item_type": "str",
      "label": "分布式worker数量",
      "require": 1,
      "choice": [],
      "range": "",
      "default": "3",
      "placeholder": "分布式训练worker的数目",
      "describe": "分布式训练worker的数目",
      "editable": 1
    }
  }
}
```

- **`--image`**：训练用的 Worker 镜像；不填时 launcher 会使用环境变量 `KFJ_TASK_IMAGES`。
- **`--working_dir`**：容器内工作目录，训练脚本和数据的路径应在此之下。
- **`--command`**：实际执行的命令（通过 `bash -c` 执行）。
- **`--num_worker`**：Worker 副本数。

保存后，在 **Pipeline 编排界面** 点击模板列表的刷新按钮，即可看到并选用「TensorFlow 分布式训练」模板。

---

## 3. 用户如何使用该任务模板

### 3.1 前置条件

- 集群已安装 Kubeflow TFJob CRD 及 Controller（`kubeflow.org/v1`，TFJob）。
- 训练代码与数据已放到某一路径，且该路径通过「数据卷/挂载目录」挂载到容器内（通常为 `/mnt/...`），并与下面填的 `--working_dir` 一致。

### 3.2 镜像要求

- **`--image`** 中的镜像需包含 TensorFlow 及你训练脚本所需的依赖。
- 可使用 [CubeStudio 基础镜像](https://github.com/data-infra/cube-studio/tree/main/images) 或官方 TensorFlow 镜像，或基于其制作自定义镜像。

### 3.3 使用步骤

1. **准备代码与数据**  
   将训练脚本（如 `mnist.py`）和数据放到某挂载目录，例如 `/mnt/{{creator}}/pipeline/example/tfjob/`，并确保该目录在任务中被挂载到容器内同一路径。

2. **新建任务并选择模板**  
   在 Pipeline 编排界面新建任务，从模板列表中选择「TensorFlow 分布式训练」（或你注册时的名称，如 tfjob）。

3. **填写参数**  
   - **镜像**：你的训练镜像地址。  
   - **启动目录**：与上面路径一致，如 `/mnt/xxx/tfjob/`。  
   - **启动命令**：例如 `python3 mnist.py` 或 `python train.py`（需使用支持多 Worker 的 TensorFlow 分布式 API，如 `tf.distribute`）。  
   - **分布式 worker 数量**：如 `2` 或 `4`。

4. **配置资源与挂载**  
   在任务配置中设置 CPU、内存、GPU（若需要）。若模板环境变量中写了 `TASK_RESOURCE_*`，会与任务配置一起决定最终 TFJob 的 resources。确保挂载包含你的 `--working_dir`。

5. **提交并查看日志**  
   提交后，Launcher 会创建名为 `tfjob-<pipeline-name>-xxxx` 的 TFJob，任务日志中会实时输出各 Worker Pod 的日志，直到训练结束。状态为 **Succeeded** 表示成功，否则为失败（Launcher 退出码 1）。

### 3.4 示例代码

可参考 Kubeflow 官方示例：[mnist_with_summaries](https://github.com/kubeflow/training-operator/blob/master/examples/tensorflow/mnist_with_summaries/mnist_with_summaries.py)，适配多 Worker 后作为启动脚本（如 `python3 mnist.py`）。
