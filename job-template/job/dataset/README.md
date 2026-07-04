# Dataset 数据集下载任务模板

本任务用于将数据集下载到指定目录，支持从 **当前平台（CubeStudio）**、**Hugging Face**、**魔塔（ModelScope）** 三种来源拉取数据。

**推荐镜像**：`ccr.ccs.tencentyun.com/cube-studio/dataset:20240501`

参数
```bash
{
    "参数": {
      "--src_type": {
            "type": "str",
            "item_type": "str",
            "label": "数据集的来源",
            "require": 1,
            "choice": ["当前平台","huggingface"],
            "range": "",
            "default": "当前平台",
            "placeholder": "",
            "describe": "数据集的来源",
            "editable": 1
        },
        "--name": {
            "type": "str",
            "item_type": "str",
            "label": "数据集的名称",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "数据集的名称",
            "editable": 1
        },
        "--version": {
            "type": "str",
            "item_type": "str",
            "label": "数据集的版本",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "latest",
            "placeholder": "",
            "describe": "数据集的版本",
            "editable": 1
        },
        "--partition": {
            "type": "str",
            "item_type": "str",
            "label": "数据集的分区，或者子数据集",
            "require": 0,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "数据集的分区，或者子数据集",
            "editable": 1
        },
        "--save_dir": {
            "type": "str",
            "item_type": "str",
            "label": "数据集的保存地址",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "",
            "placeholder": "",
            "describe": "数据集的保存地址",
            "editable": 1
        }
    }
}
```
