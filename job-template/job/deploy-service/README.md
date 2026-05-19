# 服务部署任务模板

服务部署任务模板用于在 Cube Studio 平台 pipeline中**一键创建或更新推理服务**，并自动发布上线。任务通过调用平台推理服务 API，根据「模型名 + 模型版本」判断是新建服务还是更新已有服务，完成后会触发生产环境部署。

## 前置条件

- **项目组已存在**：`--project_name` 指定的项目组必须在平台「项目组」中已创建，否则任务会报错「不存在项目组」。

## 参数说明

参数与 `launcher.py` 中的命令行参数一一对应，以下按用途分组说明。

### 模型信息

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--project_name` | 所属项目组名称，须为平台已存在的项目组 | 是 | `public` |
| `--label` | 服务中文名/描述 | 是 | `演示服务` |
| `--model_name` | 模型名，与版本一起唯一标识一个服务 | 是 | `demo` |
| `--model_version` | 模型版本号；同名+同版本会**更新**已有服务，否则**新建** | 是 | 当前日期的 `v%Y.%m.%d.1` |
| `--model_path` | 模型地址（如存储路径） | 否 | 空 |

### 服务类型与镜像

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--service_type` | 服务类型 | 是 | `serving` |
| `--images` | 推理服务使用的镜像 | 是 | `nginx` |

可选 `service_type` 示例：`serving`、`ml-server`、`tfserving`、`torch-server`、`onnxruntime`、`triton-server`、`vllm` 等，以平台实际支持为准。

### 容器运行配置

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--working_dir` | 容器工作目录 | 否 | 空 |
| `--command` | 容器启动命令 | 否 | 空 |
| `--args` | 启动参数 | 否 | 空 |
| `--env` | 环境变量（多行或 key=value） | 否 | 空 |
| `--ports` | 容器暴露端口 | 否 | `80` |

### 资源与副本

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--resource_memory` | 每个 Pod 内存 | 是 | `2G` |
| `--resource_cpu` | 每个 Pod CPU 核数 | 是 | `2` |
| `--resource_gpu` | 每个 Pod GPU 数量 | 是 | `0` |
| `--replicas` | Pod 副本数（min/max 均取此值） | 是 | `1` |

### 访问与网络

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--host` | 部署域名；留空则使用平台自动生成的域名 | 否 | 空 |

### 存储与高级配置

| 参数 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `--volume_mount` | 挂载配置，支持 pvc/hostpath/configmap，格式示例：`pvc名(pvc):/容器路径` | 否 | 空 |
| `--inference_config` | 配置文件内容，会挂载到容器 `/config/`；留空会被重置 | 否 | 空 |
| `--hpa` | 弹性伸缩配置 | 否 | 空 |
| `--metrics` | 指标采集接口，格式示例：`8080:/metrics` | 否 | 空 |
| `--health` | 健康检查，示例：`8080:/health` 或 `shell:python health.py` | 否 | 空 |

## 环境变量

任务运行时可通过环境变量控制行为：

| 变量 | 说明 |
|------|------|
| `KFJ_CREATOR` | 请求使用的创建者标识，默认 `admin`，用于 API 鉴权。 |
| `HOST` 或 `KFJ_MODEL_REPO_API_URL` | Cube Studio Dashboard 的 API 地址（不要末尾斜杠），例如 `http://kubeflow-dashboard.infra`。 |

**让任务自动使用当前访问地址**：若希望运行该模板时自动发布到当前浏览器访问的地址，可在模板的环境变量中配置 `HOST=http://xx.xx.xx.xx`，这样任务会使用该地址调用平台 API。

## 行为说明（与 launcher 一致）

1. **项目组校验**：根据 `--project_name` 查询项目组，不存在则报错并退出。
2. **创建或更新**：根据 `--model_name` + `--model_version` 查询推理服务：
   - 不存在则 **POST** 创建新服务；
   - 已存在则 **PUT** 更新该服务。
3. **发布**：创建/更新成功后等待约 5 秒，再调用部署接口将服务发布到生产环境；失败则打印错误并退出。

## 模板启动参数 JSON 配置

在平台中配置任务模板时，可使用如下结构的启动参数（与上述参数对应，便于在 UI 中展示为「模型信息」「部署信息」等分组）：

```json
{
    "模型信息": {
        "--project_name": {
            "type": "str",
            "item_type": "str",
            "label": "项目组名称",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "public",
            "placeholder": "",
            "describe": "项目组名称",
            "editable": 1
        },
        "--label": {
            "type": "str",
            "item_type": "str",
            "label": "中文描述",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "demo推理服务",
            "placeholder": "",
            "describe": "推理服务描述",
            "editable": 1
        },
        "--model_name": {
            "type": "str",
            "item_type": "str",
            "label": "模型名",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "模型名",
            "editable": 1
        },
        "--model_version": {
            "type": "str",
            "item_type": "str",
            "label": "模型版本号",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "v2022.10.01.1",
            "placeholder": "",
            "describe": "模型版本号",
            "editable": 1
        },
        "--model_path": {
            "type": "str",
            "item_type": "str",
            "label": "模型地址",
            "require": 0,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "模型地址",
            "editable": 1
        }
    },
    "部署信息": {
        "--service_type": {
            "type": "str",
            "item_type": "str",
            "label": "推理服务类型",
            "require": 1,
            "choice": ["serving", "ml-server", "tfserving", "torch-server", "onnxruntime", "triton-server", "vllm"],
            "range": "",
            "default": "serving",
            "placeholder": "",
            "describe": "推理服务类型",
            "editable": 1
        },
        "--images": {
            "type": "str",
            "item_type": "str",
            "label": "推理服务镜像",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "推理服务镜像",
            "editable": 1
        },
        "--working_dir": {
            "type": "str",
            "item_type": "str",
            "label": "推理容器工作目录",
            "require": 0,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "推理容器工作目录，如个人工作目录 /mnt/$username",
            "editable": 1
        },
        "--command": {
            "type": "str",
            "item_type": "str",
            "label": "推理容器启动命令",
            "require": 0,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "推理容器启动命令",
            "editable": 1
        },
        "--env": {
            "type": "text",
            "item_type": "str",
            "label": "推理容器环境变量",
            "require": 0,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "推理容器环境变量",
            "editable": 1
        },
        "--host": {
            "type": "str",
            "item_type": "str",
            "label": "部署域名",
            "require": 0,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "部署域名，留空自动生成",
            "editable": 1
        },
        "--ports": {
            "type": "str",
            "item_type": "str",
            "label": "推理容器暴露端口",
            "require": 0,
            "choice": [],
            "range": "",
            "default": "80",
            "placeholder": "",
            "describe": "推理容器暴露端口",
            "editable": 1
        },
        "--replicas": {
            "type": "str",
            "item_type": "str",
            "label": "pod副本数",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "1",
            "placeholder": "",
            "describe": "pod副本数",
            "editable": 1
        },
        "--resource_memory": {
            "type": "str",
            "item_type": "str",
            "label": "每个pod占用内存",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "2G",
            "placeholder": "",
            "describe": "每个pod占用内存",
            "editable": 1
        },
        "--resource_cpu": {
            "type": "str",
            "item_type": "str",
            "label": "每个pod占用cpu",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "2",
            "placeholder": "",
            "describe": "每个pod占用cpu",
            "editable": 1
        },
        "--resource_gpu": {
            "type": "str",
            "item_type": "str",
            "label": "每个pod占用gpu",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "0",
            "placeholder": "",
            "describe": "每个pod占用gpu",
            "editable": 1
        },
        "--volume_mount": {
            "type": "str",
            "item_type": "str",
            "label": "挂载",
            "require": 0,
            "choice": [],
            "range": "",
            "default": "kubeflow-user-workspace(pvc):/mnt",
            "placeholder": "",
            "describe": "容器的挂载，支持 pvc/hostpath/configmap，格式示例：$pvc_name1(pvc):/$container_path1；pvc 会自动挂载对应用户子目录",
            "editable": 1
        },
        "--inference_config": {
            "type": "text",
            "item_type": "str",
            "label": "配置文件",
            "require": 0,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "以配置文件形式挂载到容器 /config/。留空时将被自动重置。格式：---文件名\\n多行内容\\n---文件名\\n多行内容",
            "editable": 1
        },
        "--metrics": {
            "type": "str",
            "item_type": "str",
            "label": "指标采集接口",
            "require": 0,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "请求指标采集，配置端口+url，示例：8080:/metrics",
            "editable": 1
        },
        "--health": {
            "type": "str",
            "item_type": "str",
            "label": "健康检查",
            "require": 0,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "示例：8080:/health 或 shell:python health.py",
            "editable": 1
        }
    }
}
```

镜像：`ccr.ccs.tencentyun.com/cube-studio/deploy-service:20240601`
