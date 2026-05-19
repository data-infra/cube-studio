# model-register 任务模板

model-register 用于将训练完成后保存的模型**注册到平台的模型管理模块**，便于在模型仓库中统一管理、版本追溯，并可为后续的模型转换、离线预测、在线推理等环节提供模型来源。

**推荐用法**：在训练任务或流水线的下游节点中接入本模板，在训练产出模型后自动完成注册，实现「训练 → 注册 → 管理」的一体化流程。

---

## 一、设计思路

### 1.1 核心能力

- **注册/更新策略**：根据「模型名 + 当前任务 Run ID」判断是否已有记录；若无则**新建**模型记录，若有则**更新**该记录（版本、路径、指标、描述等），避免同一 Run 重复注册产生多条记录。
- **与平台打通**：通过环境变量获取当前任务上下文（创建人、项目、Run ID、流水线 ID），并调用平台模型仓库 API（`HOST` / `KFJ_MODEL_REPO_API_URL`），将模型元数据写入模型管理模块。
- **可追溯性**：注册时写入 `run_id`、`pipeline_id`，便于在模型管理中关联到具体的一次训练 Run 或流水线执行。

### 1.2 执行流程简述

1. **读取环境变量**  
   - `KFJ_CREATOR`：任务创建者（用作 API 鉴权）  
   - `KFJ_TASK_PROJECT_NAME`：任务所属项目  
   - `KFJ_RUN_ID`：当前 Run ID  
   - `KFJ_PIPELINE_ID`：所属流水线 ID（若有）  
   - `HOST` 或 `KFJ_MODEL_REPO_API_URL`：模型仓库 API 根地址，默认示例为 `http://kubeflow-dashboard.infra`  

2. **校验项目组**  
   根据参数中的 `project_name` 调用项目 API 查询，若项目不存在则直接退出，不执行注册。

3. **查询是否已注册**  
   按 `model_name` + `run_id` 查询模型管理 API，判断当前 Run 是否已注册过该模型名。

4. **创建或更新**  
   - 无记录：POST 创建新模型记录。  
   - 有记录：PUT 更新该记录（版本、路径、描述、指标、框架等）。  

5. **写入内容**  
   名称、版本、路径、描述、指标、算法框架、推理框架、run_id、pipeline_id、run_time 等，均由 launcher 从参数和环境变量中组装后提交到平台。

### 1.3 参数与 API 字段对应关系

| 启动参数 | 说明 | 写入模型管理 |
|---------|------|--------------|
| `--project_name` | 所属项目组 | 用于校验项目并关联 `project` |
| `--model_name` | 模型名 | `name` |
| `--model_version` | 模型版本号 | `version` |
| `--model_path` | 模型地址（如对象存储路径） | `path` |
| `--describe` | 模型描述 | `describe` |
| `--model_metric` | 模型指标（如 JSON 字符串） | `metrics` |
| `--framework` | 算法/训练框架 | `framework` |
| `--inference_framework` | 推理框架 | `api_type` |
| （环境变量） | Run/流水线信息 | `run_id`、`pipeline_id`、`run_time` |

---

## 二、在平台中注册该任务模板

在平台的「任务模板」或「作业模板」管理中，新增一条模板，类型/名称可使用「model-register」或「注册模型」，并做如下配置。

### 2.1 镜像

使用与当前版本匹配的镜像，例如：

```text
ccr.ccs.tencentyun.com/cube-studio/model_register:20230501
```

（实际镜像以你们仓库与版本为准。）

### 2.2 启动参数（模板配置）

在模板的「启动参数」或「参数配置」中，将下面 JSON 中的 `参数` 配置进去（一般平台会要求把键值对映射到表单或 JSON 配置里）。若平台有「从 JSON 导入」功能，可直接使用下面整段 `参数` 内容。

```json
{
    "参数": {
        "--project_name": {
            "type": "str",
            "item_type": "str",
            "label": "部署项目名",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "public",
            "placeholder": "",
            "describe": "所属项目组，需与平台已有项目组一致",
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
        "--model_version": {
            "type": "str",
            "item_type": "str",
            "label": "模型版本号",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "v2022.10.01.1",
            "placeholder": "",
            "describe": "模型版本号，如 v2022.10.01.1",
            "editable": 1
        },
        "--model_metric": {
            "type": "str",
            "item_type": "str",
            "label": "模型指标",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "如 {\"accuracy\":0.95}",
            "describe": "模型指标，可为 JSON 字符串",
            "editable": 1
        },
        "--model_path": {
            "type": "str",
            "item_type": "str",
            "label": "模型地址",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "如 minio://bucket/path/to/model",
            "describe": "模型文件/目录地址，如对象存储路径",
            "editable": 1
        },
        "--describe": {
            "type": "str",
            "item_type": "str",
            "label": "模型描述",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "模型描述",
            "editable": 1
        },
        "--framework": {
            "type": "str",
            "item_type": "str",
            "label": "模型框架",
            "require": 1,
            "choice": [
                "lr",
                "xgb",
                "tf",
                "pytorch",
                "onnx",
                "tensorrt",
                "aihub"
            ],
            "range": "",
            "default": "tf",
            "placeholder": "",
            "describe": "算法/训练框架",
            "editable": 1
        },
        "--inference_framework": {
            "type": "str",
            "item_type": "str",
            "label": "推理框架",
            "require": 1,
            "choice": [
                "serving",
                "ml-server",
                "tfserving",
                "torch-server",
                "onnxruntime",
                "triton-server",
                "aihub"
            ],
            "range": "",
            "default": "tfserving",
            "placeholder": "",
            "describe": "推理框架",
            "editable": 1
        }
    }
}
```

说明：

- `require: 1` 表示该参数在模板中为必填（具体是否强制校验以平台行为为准）。  
- `choice` 非空时，一般会在 UI 上渲染为下拉选项。  
- 若平台字段与上述不一致（如用 `required` 代替 `require`），请按平台文档做字段映射。

### 2.3 其他建议

- **执行入口**：若模板需要指定启动命令，一般为执行 `launcher.py`，例如：`python launcher.py`（具体以镜像内入口为准）。  
- **网络**：任务需能访问模型仓库 API（即 `HOST` / `KFJ_MODEL_REPO_API_URL`），注意命名空间、网络策略是否放行。

---

## 三、用户如何使用该任务模板

### 3.1 典型场景：训练完成后注册

1. **在流水线中**  
   - 上游节点：训练任务，将模型保存到某路径（如对象存储 `minio://bucket/project/run_id/model`）。  
   - 下游节点：选择「model-register」任务模板，填写参数（见下），并保证该节点能拿到上游输出的模型路径。

2. **单独创建一次「注册模型」任务**  
   - 当模型已存在于某路径（例如历史训练产出、从别处拷贝到对象存储），可单独创建一次 model-register 任务，只填本次注册所需参数即可。

### 3.2 参数怎么填

| 参数 | 说明 | 示例 |
|------|------|------|
| 部署项目名 | 平台中已存在的项目组，与「模型管理」中的项目一致 | `public`、`my-project` |
| 模型名 | 唯一标识该模型的名称，建议 a-z、0-9、-，最长 54 字符 | `iris-classifier`、`recommend-v1` |
| 模型版本号 | 便于区分的版本字符串 | `v2022.10.01.1`、`v1.0.0` |
| 模型地址 | 训练产出模型所在路径（对象存储或平台可访问路径） | `minio://bucket/path/to/saved_model` |
| 模型指标 | 可选，训练得到的指标，可 JSON | `{"accuracy":0.95,"auc":0.88}` |
| 模型描述 | 简短说明 | `iris 分类模型 v1` |
| 模型框架 | 训练/算法框架 | `tf`、`pytorch`、`onnx` 等 |
| 推理框架 | 后续推理使用的框架 | `tfserving`、`torch-server`、`onnxruntime` 等 |

### 3.3 与流水线/训练 Run 的关联

- 在流水线或训练任务中执行 model-register 时，平台会注入 `KFJ_RUN_ID`、`KFJ_PIPELINE_ID` 等环境变量，launcher 会把这些信息写入模型记录，便于在模型管理中看到「来自哪次 Run / 哪条流水线」。
- 同一 Run 内多次用**相同 model_name** 执行注册，会**更新**同一条模型记录而不是新增多条。

### 3.4 命令行示例（仅作理解用）

若直接在镜像内用命令行调试，等价形式类似（实际以平台生成的启动命令为准）：

```bash
python launcher.py \
  --project_name public \
  --model_name my-model \
  --model_version v2022.10.01.1 \
  --model_path minio://bucket/path/to/model \
  --model_metric '{"accuracy":0.95}' \
  --describe "我的模型描述" \
  --framework pytorch \
  --inference_framework torch-server
```

### 3.5 使用注意

- **项目组**：`project_name` 必须在平台「项目/项目组」中已存在，否则会报「不存在项目组」并退出。  
- **模型路径**：`model_path` 必须是任务运行环境可访问的路径（如集群内 MinIO、NFS 等），模型管理只存路径与元数据，不在此步骤上传文件。  
- **权限**：任务使用的身份（对应 `KFJ_CREATOR`）需有模型仓库 API 的调用权限，否则会注册/更新失败。

按上述方式在平台注册模板并配置参数后，用户即可在流水线或单次任务中通过「model-register」将训练好的模型注册到模型管理模块，并在模型管理中进行版本管理与后续使用。
