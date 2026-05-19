# Ray 任务模板

基于 [Ray](https://www.ray.io/) 的 Python 多机分布式计算任务模板，用于在 Kubernetes 上按需拉起 Ray 集群并执行用户代码。

---

## 一、设计思路

### 1.1 整体流程

- **执行角色**：流水线中的「Ray 任务」节点会启动一个 Pod，该 Pod 内运行 `launcher.py`，既作为**驱动端**（负责创建集群、执行用户命令），也作为连接 Ray 的**客户端**。
- **集群形态**：Launcher 通过 K8s API 在当前命名空间下创建一套 Ray 集群：
  - **1 个 Head**：1 个 Deployment + 1 个 Service，Head 容器内执行 `ray start --head --port=6379 ... --block`。
  - **N 个 Worker**：1 个 Deployment（replicas=N），每个 Worker 容器内执行 `ray start --address=<head>:6379 ... --block`。
- **命名规则**：Head 名称形如 `ray-header-<pipeline_name>-<task_id>`（截断至 54 字符），Worker 名称将 `header` 替换为 `worker`，便于同一任务唯一标识。
- **执行顺序**：
  1. 清理同名的旧 Head Service / Head Deployment / Worker Deployment（若存在）；
  2. 创建 Head Service → Head Deployment → Worker Deployment，等待一段时间；
  3. Launcher 通过 `ray.util.connect(<head>:10001)` 连接集群，并轮询直到集群内节点数达到配置的 Worker 数量；
  4. （可选）在当前 Pod 内执行「初始化脚本」；
  5. 设置环境变量 `RAY_HOST=<head 服务名>`，在指定工作目录下执行**用户命令**（如 `python demo.py`）；
  6. 用户代码中通过 `RAY_HOST` 连接同一 Ray 集群，使用 `@ray.remote` 等编写分布式逻辑。

因此，**用户无需事先部署 Ray 集群**，只要在流水线里配置好镜像、Worker 数量、工作目录和启动命令即可。

### 1.2 资源与调度

- **CPU/内存**：Head 与 Worker 的 requests/limits 来自任务模板配置的环境变量（如 `KFJ_TASK_RESOURCE_CPU`、`KFJ_TASK_RESOURCE_MEMORY`），Head 还会把 `--num-cpus` 设为容器 CPU request。
- **GPU**：若配置了 GPU（`KFJ_TASK_RESOURCE_GPU`），Worker 会申请对应 GPU 资源并设置 `GPU_NUM`；无 GPU 时 Worker 会设置 `NVIDIA_VISIBLE_DEVICES=none`；特殊值 -1 时使用 privileged 容器。
- **节点选择**：Head 与 Worker 使用相同的 `KFJ_TASK_NODE_SELECTOR` 做节点亲和，并带有「尽量打散到不同节点」的 podAntiAffinity（按 hostname）。
- **存储**：通过 `KFJ_TASK_VOLUME_MOUNT` 解析出的卷会挂载到 Head 与 Worker，便于代码和数据访问。

### 1.3 Head 服务端口

- `10001`：Ray 客户端连接端口（用户代码连接集群用）；
- `8265`：Ray Dashboard；
- `6379`：Ray 内部 Redis。

用户代码只需使用 **`<RAY_HOST>:10001`** 连接即可。

### 1.4 初始化脚本（--init）

- 在 **Head 和每个 Worker** 的启动命令中，会先执行 `bash <init 脚本> &&`，再执行 `ray start ...`，用于在每台节点上安装依赖或做环境准备。
- Launcher 还会在**当前驱动 Pod** 内单独执行一次该初始化脚本，再执行用户命令，保证驱动端环境一致。

---

## 二、在任务模板中注册与配置

### 2.1 启动参数（job_template_args）

- **镜像**：`ccr.ccs.tencentyun.com/cube-studio/ray:gpu-20250301`（以实际 init-job-template 为准）。
- **账号**：`kubeflow-pipeline`。
- 环境变量示例（用于资源与节点调度）：
  - `NO_RESOURCE_CHECK=true`
  - `TASK_RESOURCE_CPU=2`
  - `TASK_RESOURCE_MEMORY=4G`
  - `TASK_RESOURCE_GPU=0`

Launcher 通过命令行参数接收配置，平台会把「任务模板参数」转成 launcher 的命令行参数。参数需与 `launcher.py` 中 `argparse` 一致：

| 平台参数名   | Launcher 参数   | 含义 |
|-------------|----------------|------|
| `images`    | （镜像由平台注入，launcher 用 `KFJ_TASK_IMAGES`） | 任务使用的镜像，建议基于官方 Ray 镜像封装 |
| `--workdir` | `--workdir`    | 工作目录，用户命令在该目录下执行 |
| `--init`    | `--init`       | 初始化脚本路径（宿主机路径），Head/Worker 启动前及当前 Pod 内各执行一次 |
| `--command` | `--command`    | 用户启动命令，如 `python demo.py` |
| `--num_worker` | `--num_worker` | Worker 数量（launcher 内部变量为 `NUM_WORKER`） |

在 `job_template_args` 中按「参数组」组织（如 `"分布式任务"`），每个参数需包含 `type`、`label`、`require`、`default`、`describe`、`editable` 等字段；`item_type` 为 `workdir` 的会做路径选择器。示例结构（仅示意，以实际 `init-job-template.json` 为准）：

```json
"job_template_args": {
  "分布式任务": {
    "images": { "type": "str", "item_type": "image", "label": "镜像", "require": 0, "default": "ccr.ccs.tencentyun.com/cube-studio/ray:gpu-20250301", ... },
    "--workdir": { "type": "str", "item_type": "workdir", "label": "启动目录", "require": 1, "default": "/mnt/{{creator}}/pipeline/example/ray/", ... },
    "--init": { "type": "str", "item_type": "workdir", "label": "初始化脚本", "require": 0, "default": "", ... },
    "--command": { "type": "str", "item_type": "str", "label": "启动命令", "require": 1, "default": "python demo.py", ... },
    "--num_worker": { "type": "str", "label": "机器数量", "require": 1, "default": "3", "regex": "^[0-9]*$", ... }
  }
}
```

### 2.2 环境变量（可选）

任务节点可配置环境变量，launcher 会读取的包括：

- `KFJ_NAMESPACE`、`KFJ_TASK_ID`、`KFJ_PIPELINE_NAME`、`KFJ_TASK_IMAGES`、`KFJ_TASK_VOLUME_MOUNT`
- `KFJ_TASK_RESOURCE_CPU`、`KFJ_TASK_RESOURCE_MEMORY`、`KFJ_TASK_RESOURCE_GPU`
- `KFJ_TASK_NODE_SELECTOR`、`GPU_RESOURCE_NAME`、`DEFAULT_POD_RESOURCES`、`HUBSECRET` 等

无需在 README 中全部列出，按需在「任务模板」或「运行环境」中说明即可。

---

## 三、用户如何使用该任务模板

### 3.1 在流水线中使用

1. 在流水线编辑器中添加「Ray」任务节点（从任务模板中选择 ray 模板）。
2. 配置参数：
   - **启动目录（--workdir）**：放代码和数据的目录，如 `/mnt/<用户名>/pipeline/example/ray/`。
   - **启动命令（--command）**：在 workdir 下要执行的命令，如 `python demo.py` 或 `python job_example.py`。
   - **机器数量（--num_worker）**：Worker 数量，与 launcher 的 `NUM_WORKER` 一致，决定 Ray 集群规模。
   - **镜像（images）**：可选，使用自带依赖的镜像时填写。
   - **初始化脚本（--init）**：可选，Head/Worker 及当前 Pod 会执行，用于安装包或准备环境。

3. 配置资源：在任务/节点上设置 CPU、内存、GPU 等，这些会通过环境变量传给 launcher，并应用到 Head 与 Worker Pod。

4. 保存并运行流水线。Launcher 会先创建 Ray 集群，再执行用户命令；用户代码通过 `RAY_HOST` 连接集群。

### 3.2 用户代码写法

- 在**集群模式**下，launcher 会设置环境变量 `RAY_HOST=<head 服务名>`（仅服务名，无端口）。用户代码应使用 **`<RAY_HOST>:10001`** 连接。
- 若希望同一份代码在本地也能调试，可根据是否存在 `RAY_HOST` 判断是连接已有集群还是本地 `ray.init()`。

示例（与 `job_example.py` 一致）：

```python
import os
import ray

@ray.remote
def fun1(arg):
    # 耗时任务；函数内尽量只使用局部变量
    return "back_data"

def main():
    tasks = [fun1.remote(i) for i in range(100)]
    results = ray.get(tasks)

if __name__ == "__main__":
    head_service = os.getenv("RAY_HOST", "")
    if head_service:
        # 集群模式：launcher 已创建集群并设置 RAY_HOST
        ray.util.connect(head_service + ":10001")
    else:
        # 本地调试
        ray.init()
    main()
```

注意：同一命名空间下，Pod 间通过服务名访问，因此直接使用 `RAY_HOST + ":10001"` 即可，无需加 `.pipeline` 等后缀（除非平台有特殊 DNS 约定）。

### 3.3 依赖

- 镜像中需已安装 `ray`（如 `pip install ray`）。
- 若使用自定义镜像，建议以官方 Ray 镜像为基础并保持 Ray 版本兼容。

### 3.4 参考示例

- 目录下的 `job_example.py` 为多节点示例：通过 `@ray.remote` 在多个节点上执行任务并收集结果，连接方式与上面一致。
- `demo.py` 可作为更简化的示例参考。
