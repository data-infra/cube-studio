import json
dataset = json.load(open('identity-src.json'))
for sample in dataset:
    sample["output"] = sample["output"].replace("{{name}}", 'CubeStudio智能助手').replace("{{author}}", 'CubeStudio开源社区')
json.dump(dataset, open("identity.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
