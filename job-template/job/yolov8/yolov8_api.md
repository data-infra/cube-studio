
## 推理接口

通过该接口将媒体内容发送给inference接口，进行模型推理，获取推理后的结果

- **URL**：/v1/models/MODEL_NAME/versions/MODEL_VERSION/predict
- **Method**：POST
- **Content-Type**： application/json
- **需要登录**：否

## headers
```
{
    'Content-Type': 'application/json'
}
```
## 输入
```bash
{
    "image":base64.b64encode(open(image_path, "rb").read()).decode('utf-8')
}
```

## 输出

**状态码**：200 OK  

```
{
    "labels":[],
    "scores":[],
    "xywhs":[],
    "orig_shape":[orig_width,orig_height]
}
```

## 其他推理类型示例接口

通过该接口将媒体内容发送给inference接口，进行模型推理，获取推理后的结果

- **URL**：/predict
- **Method**：POST
- **Content-Type**： application/json
- **需要登录**：否

## headers
```
{
    'Content-Type': 'application/json'
}
```
## 输入
```bash
{
    "image":base64.b64encode(open(image_path, "rb").read()).decode('utf-8')
}
```

## 输出

**状态码**：200 OK  

```
{
    "results":[],
}
```

# python调用示例

```python
import requests, base64, json
image_path = "https://cube-studio.oss-cn-hangzhou.aliyuncs.com/pipeline/media-download/train2014/COCO_train2014_000000000597.jpg"
url = "http://xx.xx.xx.xx/predict"
data = {"image": base64.b64encode(open(image_path, "rb").read()).decode('utf-8')}
headers = {'Content-Type': 'application/json'}
response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
```

# 自动化标注接口
```
/labelstudio
```