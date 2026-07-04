# 视频/多媒体任务模板（video-audio 目录）

本目录提供三个**分布式多媒体任务模板**，均基于 **Ray** 在 K8s 上拉起多 Worker 并行执行，对应入口脚本与用途如下：

| 任务模板         | 入口脚本              | 功能说明                 |
|------------------|-----------------------|--------------------------|
| **media-download** | `start_download.py`   | 分布式下载媒体文件（URL → 本地） |
| **video-img**      | `start_video_img.py`  | 分布式视频抽帧（视频 → 图片序列） |
| **video-audio**    | `start_video_audio.py`| 分布式视频提取音频（视频 → 音频） |

---

## 一、各任务模板的设计思路

### 1. media-download（分布式媒体文件下载）

- **目标**：根据配置列表，将大量媒体 URL 下载到指定本地路径，利用多机多 Worker 提高吞吐。
- **实现要点**：
  - 使用 **Ray** 在 K8s 上创建 Ray 集群（`ray_launcher`），Worker 数量由参数 `--num_worker` 指定。
  - 从 `--input_file` 读取每行 `$url $local_path`，按行轮询划分到约 1000 个“任务盒”，再把这些任务盒作为 Ray 远程任务下发到各 Worker。
  - 每个 Worker 内用 `requests.get` 下载，已存在的 `local_path` 会跳过；会按需创建 `local_path` 的父目录。
- **适用场景**：大批量图片/视频/音频 URL 的离线下载、数据同步等。

### 2. video-img（分布式视频抽帧）

- **目标**：对多路视频按指定帧率抽帧为图片序列，通过多 Worker 并行处理多文件。
- **实现要点**：
  - 同样使用 **Ray** 创建集群，从 `--input_file` 读取每行：`$local_video_path $des_img_dir $frame_rate`。
  - 任务划分方式与 media-download 一致（轮询到约 1000 个任务盒再分发）。
  - 每个任务在 Worker 内用 **ffmpeg** 执行：  
    `ffmpeg -i <视频> -r <帧率> -f image2 <输出目录>/%5d.jpg`，自动创建输出目录。
- **适用场景**：视频拆帧做目标检测、关键帧分析、缩略图生成等。

### 3. video-audio（分布式视频提取音频）

- **目标**：从多路视频中批量提取音频（mp3 或 wav），多 Worker 并行。
- **实现要点**：
  - Ray 集群与任务划分方式同上，输入文件每行格式：`$local_video_path $des_audio_path`。
  - 若目标为 **.mp3**：直接 `ffmpeg` 从视频导出 mp3。
  - 若目标为 **.wav**：先导出为 mp3，再转为 16kHz、单声道、pcm_s16le 的 wav（常用于语音识别），最后删除中间 mp3。
  - 若 `des_audio_path` 已存在则跳过该条。
- **适用场景**：视频转音频、语音识别数据准备等。

---

## 二、在平台中注册与配置任务模板

三个模板均在平台的 **任务模板** 中注册，配置来源为初始化配置（如 `init-job-template.json`）。若需在平台里新增或修改这些模板，可按下面方式操作。

### 2.1 注册入口与前置条件

- **入口**：CubeStudio → **训练** → **任务模板** → **添加**（或通过初始化数据自动创建）。
- **前置**：
  - 镜像已存在并可被集群拉取（本组模板共用镜像，如 `ccr.ccs.tencentyun.com/cube-studio/video-audio:20260301`）。
  - 若镜像为私有，需先在 **训练 → 仓库** 中配置仓库账号，并在 **训练 → 镜像** 中添加该镜像。

### 2.2 各模板在配置中的关键字段

三个模板共用同一镜像与 git 路径，通过 **名称 + 启动命令 + 参数** 区分：

| 配置项 | media-download | video-img | video-audio |
|--------|----------------|-----------|-------------|
| **job_template_name** | `media-download` | `video-img` | `video-audio` |
| **job_template_command** | `python start_download.py` | `python start_video_img.py` | `python start_video_audio.py` |
| **gitpath** | `/job-template/job/video-audio` | 同上 | 同上 |
| **image_name** | 同上（video-audio 镜像） | 同上 | 同上 |
| **job_template_volume** | 空（可按需挂载工作目录） | 空 | 空 |
| **job_template_account** | `kubeflow-pipeline` | `kubeflow-pipeline` | `kubeflow-pipeline` |

### 2.3 启动参数（job_template_args）

- **media-download**
  - `--num_worker`：Worker 数量，默认 `3`。
  - `--download_type`：下载类型，当前仅 `url`。
  - `--input_file`：配置文件路径（如 `/mnt/{{creator}}/pipeline/example/media/video_url.txt`），内容格式见下文“使用方式”。

- **video-img**
  - `--num_worker`：Worker 数量，默认 `3`。
  - `--input_file`：配置文件路径（如 `/mnt/{{creator}}/pipeline/example/media/video_image.txt`），每行：`$local_video_path $des_img_dir $frame_rate`。

- **video-audio**
  - `--num_worker`：Worker 数量，默认 `3`。
  - `--input_file`：配置文件路径（如 `/mnt/{{creator}}/pipeline/example/media/video_audio.txt`），每行：`$local_video_path $des_audio_path`。

在「添加/编辑任务模板」时，**目录** 填上述 `gitpath`，**启动命令** 填对应 `job_template_command`，**启动参数** 按平台要求配置为上述 args（通常以 JSON 形式配置分组与默认值）。

### 2.4 扩展与帮助链接

- **expand** 中可设置 `index`（同组内排序）、`help_url`（帮助文档路径，如 `/job-template/job/video-audio`），便于在编排界面展示与跳转。

---

## 三、用户如何使用各任务模板

### 3.1 在流水线中选用模板

1. 打开 **CubeStudio** → **训练** → **流水线（Pipeline）** 编排页。
2. 在模板列表中点击 **刷新**，找到「视频处理」下的 **media-download**、**video-img**、**video-audio**。
3. 将对应模板拖入画布，在节点上填写本小节所述的参数与输入文件。

### 3.2 media-download

- **参数**：
  - **worker数量**（`--num_worker`）：建议按数据量和集群资源设置，如 `3`。
  - **配置文件地址**（`--input_file`）：宿主机或挂载卷上的文本文件路径，须能被任务容器访问（建议放在 `/mnt/{{creator}}/...` 等挂载目录下）。
- **input_file 格式**（每行一条，空格或制表符分隔）：
  ```text
  $url $local_path
  ```
  - `$url`：媒体文件 URL。
  - `$local_path`：下载到容器内的本地路径；父目录会自动创建；若文件已存在则跳过。
- **示例**：
  ```text
  https://example.com/video1.mp4 /mnt/admin/pipeline/media/video1.mp4
  https://example.com/audio2.mp3 /mnt/admin/pipeline/audio/audio2.mp3
  ```

### 3.3 video-img

- **参数**：
  - **worker数量**（`--num_worker`）：如 `3`。
  - **配置文件地址**（`--input_file`）：同上，须可访问。
- **input_file 格式**（每行一条）：
  ```text
  $local_video_path $des_img_dir $frame_rate
  ```
  - `$local_video_path`：容器内视频文件路径。
  - `$des_img_dir`：输出图片目录（如 `/mnt/admin/pipeline/frames/video1`），会生成 `00001.jpg`, `00002.jpg`, ...。
  - `$frame_rate`：抽帧率，如 `1` 表示每秒 1 帧。
- **示例**：
  ```text
  /mnt/admin/pipeline/media/video1.mp4 /mnt/admin/pipeline/frames/v1 1
  /mnt/admin/pipeline/media/video2.mp4 /mnt/admin/pipeline/frames/v2 2
  ```

### 3.4 video-audio

- **参数**：
  - **worker数量**（`--num_worker`）：如 `3`。
  - **配置文件地址**（`--input_file`）：同上。
- **input_file 格式**（每行一条）：
  ```text
  $local_video_path $des_audio_path
  ```
  - `$local_video_path`：容器内视频路径。
  - `$des_audio_path`：输出音频路径；支持 `.mp3` 或 `.wav`。若为 `.wav`，会转为 16kHz 单声道。文件已存在则跳过。
- **示例**：
  ```text
  /mnt/admin/pipeline/media/video1.mp4 /mnt/admin/pipeline/audio/video1.mp3
  /mnt/admin/pipeline/media/video2.mp4 /mnt/admin/pipeline/audio/video2.wav
  ```

### 3.5 使用注意

- **挂载与路径**：若需持久化，输入/输出路径应落在平台挂载的目录下（如 `/mnt/{{creator}}/...`），具体以实际挂载为准。
- **依赖**：video-img、video-audio 依赖容器内已安装 **ffmpeg**；当前镜像已包含。
- **串联使用**：可先用 **media-download** 把 URL 下载到本地，再在后续节点用 **video-img** 或 **video-audio** 对本地视频做抽帧或提音频；只需保证同一流水线内挂载一致、路径可被后续任务访问即可。

---

## 四、目录与脚本对应关系小结

| 任务模板         | 入口脚本              | 输入文件格式 |
|------------------|-----------------------|----------------|
| media-download   | `start_download.py`   | 每行：`$url $local_path` |
| video-img        | `start_video_img.py`  | 每行：`$local_video_path $des_img_dir $frame_rate` |
| video-audio      | `start_video_audio.py`| 每行：`$local_video_path $des_audio_path` |

三个脚本均通过 `--num_worker` 控制 Ray Worker 数量，通过 `--input_file` 指定上述格式的配置文件路径