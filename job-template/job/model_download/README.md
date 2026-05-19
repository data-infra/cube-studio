# model-download 任务模板

model-download 用于**从多种来源下载模型到指定目录**：支持从平台「模型管理」、平台「推理服务」、Hugging Face、魔塔（ModelScope）拉取模型，便于在流水线或单机任务中统一做模型导入与后续转换、评估、推理。

**推荐用法**：在流水线首节点用本模板拉取基线模型，或作为「模型管理/推理服务 → 本地目录」的导出步骤；也可单独创建任务从 Hugging Face/魔塔下载公开模型。

---

## 一、设计思路

### 1.1 核心能力

- **多源统一入口**：通过参数 `--from` 选择来源（模型管理、推理服务、huggingface、魔塔），同一套任务模板覆盖平台内与平台外模型获取。
- **与平台打通**：当来源为「模型管理」或「推理服务」时，通过平台 API 查询模型/推理服务的路径信息（使用 `HOST` / `KFJ_MODEL_REPO_API_URL` 与 `KFJ_CREATOR` 鉴权），再根据 path 类型自动选择「HTTP 下载」或「本地拷贝」到 `--save_path`。
- **多子模型支持**：若平台中模型/推理服务的 path 为 JSON（多个子模型），可通过 `--sub_model_name` 指定要下载的子模型对应的路径。
- **元信息落盘**：从「模型管理」下载时，会将该模型在平台上的元数据（如 name、version、path、framework 等）写入 `save_path` 下的 `{name}.{version}.json`，便于下游任务或指标计算使用。

### 1.2 支持的来源与行为

| 来源（--from） | 行为简述 |
|----------------|----------|
| **模型管理**   | 调用 `training_model_modelview` API，按「模型名 + 版本」查询，取 `path`；若 path 为 JSON 则用 `sub_model_name` 取子路径；path 为 URL 则 HTTP 下载，为本地路径则拷贝到 save_path；并写入 `{name}.{version}.json`。 |
| **推理服务**   | 调用 `inferenceservice_modelview` API，按「模型名 + 版本 + 可选 model_status」查询，取 `model_path`；同样支持 JSON 子模型与 URL/本地路径的下载或拷贝。 |
| **huggingface**| 使用 `huggingface-cli download`，将指定 `model_name`（及可选 `model_version` 作 revision）下载到 `save_path`，支持断点续传。 |
| **魔塔**       | 使用 `modelscope download`，将指定 `model_name` 下载到 `save_path`。 |

### 1.3 环境变量

launcher 依赖以下环境变量（平台任务通常会自动注入）：

- **KFJ_CREATOR**：任务创建者，用于调用平台 API 时的鉴权。
- **HOST** 或 **KFJ_MODEL_REPO_API_URL**：平台 API 根地址，默认示例为 `http://kubeflow-dashboard.infra`（仅「模型管理」「推理服务」需要）。

Hugging Face 相关环境（如镜像内或模板中可配置）：

- **HF_ENDPOINT**：可选，镜像/模板中常配置为 `https://hf-mirror.com` 等镜像站以加速。
- **HF_HUB_ENABLE_HF_TRANSFER**：可选，用于启用 hf_transfer 加速。

---

## 二、在任务模板中注册配置

在平台的「任务模板」管理中，新增或编辑「model-download」模板，做如下配置。

### 2.1 镜像

使用与当前版本匹配的镜像，例如：

```text
ccr.ccs.tencentyun.com/cube-studio/model_download:20250301
```

（实际以你们仓库与版本为准。）

### 2.2 启动命令

```text
python3 launcher.py
```

### 2.3 挂载与环境（建议）

- **卷挂载**：若希望下载到集群内持久化目录，可配置 hostPath 或 PVC 挂载到容器内某目录，并将该目录作为 `--save_path` 使用，例如：`/data/k8s/kubeflow/pipeline/workspace/(hostpath):/mnt/`。
- **环境变量**：若主要从 Hugging Face 下载，可配置 `HF_ENDPOINT`、`HF_HUB_ENABLE_HF_TRANSFER` 等（见上）。

### 2.4 启动参数（模板配置）

在模板的「启动参数」或「参数配置」中，将下面 JSON 中的 `参数` 配置进去；若平台支持「从 JSON 导入」，可直接使用下面整段 `参数` 内容。

```json
{
    "参数": {
        "--from": {
            "type": "str",
            "item_type": "str",
            "label": "模型来源",
            "require": 1,
            "choice": ["模型管理", "推理服务", "huggingface", "魔塔"],
            "range": "",
            "default": "模型管理",
            "placeholder": "",
            "describe": "模型来源地",
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
            "placeholder": "a-z、0-9、- 组成，最长54字符",
            "describe": "模型名(a-z0-9-字符组成，最长54个字符)",
            "editable": 1
        },
        "--sub_model_name": {
            "type": "str",
            "item_type": "str",
            "label": "子模型名",
            "require": 0,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "子模型名，对包含多个子模型的模型/推理服务时填写",
            "editable": 1
        },
        "--model_version": {
            "type": "str",
            "item_type": "str",
            "label": "模型版本号",
            "require": 0,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "如 v2022.10.01.1 或 Hugging Face revision",
            "describe": "模型版本号；来自 Hugging Face 时可为 revision（如 main、v1.0）",
            "editable": 1
        },
        "--model_status": {
            "type": "str",
            "item_type": "str",
            "label": "模型状态",
            "require": 0,
            "choice": ["online", "offline", "test"],
            "range": "",
            "default": "online",
            "placeholder": "",
            "describe": "模型状态，仅当来源为「推理服务」时有效",
            "editable": 1
        },
        "--save_path": {
            "type": "str",
            "item_type": "str",
            "label": "下载目的目录",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "/mnt/xx/download/model/",
            "placeholder": "如 /mnt/workspace/model",
            "describe": "模型下载到的本地目录",
            "editable": 1
        }
    }
}
```

说明：

- `require: 1` 表示该参数在模板中为必填（具体是否强制校验以平台为准）。
- `choice` 非空时，一般会在 UI 上渲染为下拉选项。
- 若平台字段与上述不一致（如用 `required` 代替 `require`），请按平台文档做字段映射。

### 2.5 其他注意

- **网络**：从「模型管理」「推理服务」下载时，任务需能访问平台 API；从 Hugging Face/魔塔 下载时，需能访问外网或对应镜像站。
- **权限**：使用「模型管理」「推理服务」时，`KFJ_CREATOR` 对应身份需有相应 API 的查询权限。

---

## 三、用户如何使用该任务模板

### 3.1 按来源使用

#### 从「模型管理」下载

1. 在平台「模型管理」中已有注册的模型（含名称、版本、path）。
2. 创建 model-download 任务，选择来源 **模型管理**，填写：
   - **模型名**、**模型版本号**：与模型管理中的一致。
   - **子模型名**：仅当该模型在平台中 path 为 JSON 且包含多个子模型时填写，用于指定要下载的子模型键名。
   - **保存目录**：容器内可写目录，建议使用挂载的持久化路径（如 `/mnt/workspace/model`）。

#### 从「推理服务」下载

1. 在平台已部署推理服务，且服务配置了模型路径。
2. 创建 model-download 任务，选择来源 **推理服务**，填写：
   - **模型名**、**模型版本号**：与推理服务中的 model_name、model_version 一致。
   - **模型状态**：可选，如 `online`、`offline`、`test`，用于过滤推理服务。
   - **子模型名**：仅当 model_path 为 JSON 多子模型时填写。
   - **保存目录**：同上。

#### 从 Hugging Face 下载

1. 创建 model-download 任务，选择来源 **huggingface**，填写：
   - **模型名**：Hugging Face 仓库名，如 `bert-base-chinese`、`meta-llama/Llama-2-7b-hf`。
   - **模型版本号**：可选，对应 `--revision`（如 `main`、`v1.0`），不填则使用默认分支。
   - **保存目录**：同上。
2. 若需加速，确保任务环境或模板中配置了 `HF_ENDPOINT`（如 `https://hf-mirror.com`）等。

#### 从魔塔（ModelScope）下载

1. 创建 model-download 任务，选择来源 **魔塔**，填写：
   - **模型名**：ModelScope 模型 ID，如 `damo/nlp_structbert_zero-shot-classification_english-base`。
   - **保存目录**：同上。
2. **模型版本号** 在魔塔场景下由 modelscope 内部处理，可不填或按平台占位填写。

### 3.2 参数速查

| 参数           | 说明 | 模型管理/推理服务 | Hugging Face | 魔塔 |
|----------------|------|-------------------|--------------|------|
| 模型来源       | 选择下载来源 | 模型管理 或 推理服务 | huggingface | 魔塔 |
| 模型名         | 模型标识 / 仓库名 / 模型 ID | 必填 | 必填 | 必填 |
| 子模型名       | 多子模型时的键名 | 按需 | - | - |
| 模型版本号     | 版本 / revision | 建议填 | 可选（revision） | 可选 |
| 模型状态       | online/offline/test | - | - | - |
| 下载目的目录   | 保存路径 | 必填 | 必填 | 必填 |

### 3.3 命令行示例（仅作理解用）

实际以平台生成的启动命令为准，等价形式示例：

**从模型管理：**
```bash
python3 launcher.py --from 模型管理 --model_name my-model --model_version v1.0 --save_path /mnt/workspace/model
```

**从推理服务：**
```bash
python3 launcher.py --from 推理服务 --model_name my-model --model_version v1.0 --model_status online --save_path /mnt/workspace/model
```

**从 Hugging Face：**
```bash
python3 launcher.py --from huggingface --model_name bert-base-chinese --model_version main --save_path /mnt/workspace/model
```

**从魔塔：**
```bash
python3 launcher.py --from 魔塔 --model_name damo/nlp_structbert_zero-shot-classification_english-base --save_path /mnt/workspace/model
```

### 3.4 使用注意

- **保存目录**：`save_path` 需在容器内存在且可写；若使用挂载卷，请填写挂载后的路径（如 `/mnt/workspace/model`）。
- **平台来源**：从「模型管理」「推理服务」时，模型/推理服务在平台中的 path 必须已配置；path 为 URL 时会发起 HTTP 下载，为服务器本地路径时会在同机拷贝（任务需能访问该路径）。
- **多子模型**：仅当平台中 path 为 JSON 且需要其中某一个子路径时再填 `sub_model_name`，否则留空。
- **Hugging Face/魔塔**：需保证运行环境能访问对应站点（或镜像）；大规模模型建议配合断点续传与足够磁盘空间。

按上述方式在平台注册并配置 model-download 模板后，用户即可在流水线或单次任务中从「模型管理」「推理服务」、Hugging Face、魔塔下载模型到指定目录，用于后续转换、评估或推理。
