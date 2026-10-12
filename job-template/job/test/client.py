"""调用 server.py 的 /predict 推理接口的最小示例。"""

import requests,json

# 10 个特征的假数据，字段名与 feature_names.json 对齐
sample = {
    "age": 30, "duration": 487, "campaign": 2, "pdays": 999, "previous": 0,
    "emp_var_rate": -1.8, "cons_price_idx": 92.893, "cons_conf_idx": -46.2,
    "euribor3m": 1.313, "nr_employed": 5099.1,
}

# 调用单样本预测接口并打印结果
resp = requests.post("http://127.0.0.1:5000/predict", json=sample, timeout=10)
print(resp.status_code)
print(json.dumps(resp.json(),indent=4,ensure_ascii=False))
