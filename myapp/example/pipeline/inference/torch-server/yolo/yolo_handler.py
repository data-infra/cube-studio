import io
import os
import json
import base64
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image
import torch
from ultralytics import YOLO

def _extract_image_bytes(item: Any) -> Tuple[Optional[bytes], Optional[Dict[str, Any]]]:
    """
    支持：
      - 直接二进制（curl -T file.jpg）
      - {"body": bytes} / {"data": bytes}
      - JSON: {"img":"<base64>", "imgsz":640, "conf":0.25, "iou":0.45}
    返回: (image_bytes | None, overrides | None)
    """
    if isinstance(item, (bytes, bytearray)):
        return bytes(item), None

    if isinstance(item, dict):
        # 先取二进制
        for k in ("body", "data"):
            if k in item and isinstance(item[k], (bytes, bytearray)):
                return bytes(item[k]), None

        # 尝试 JSON
        jb = item.get("body") or item.get("data")
        jd = None
        if isinstance(jb, (bytes, bytearray)):
            try:
                jd = json.loads(jb.decode("utf-8"))
            except Exception:
                return bytes(jb), None
        elif isinstance(jb, str):
            jd = json.loads(jb)
        elif "img" in item:   # 直接就是 JSON
            jd = item

        if isinstance(jd, dict):
            img_b64 = jd.get("img")
            if img_b64:
                return base64.b64decode(img_b64), {
                    "imgsz": jd.get("imgsz"),
                    "conf": jd.get("conf"),
                    "iou":  jd.get("iou"),
                }
            return None, {
                "imgsz": jd.get("imgsz"),
                "conf": jd.get("conf"),
                "iou":  jd.get("iou"),
            }

    return None, None

# ====== 服务单例 ======
class _Service:
    def __init__(self):
        self.initialized = False
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.names = None
        # 默认参数，可用环境变量覆盖
        self.default_imgsz = int(os.getenv("TS_IMGSZ", "640"))
        self.default_conf  = float(os.getenv("TS_CONF", "0.25"))
        self.default_iou   = float(os.getenv("TS_IOU", "0.45"))

    def initialize(self, context):
        props = context.system_properties
        model_dir = props.get("model_dir")
        manifest  = context.manifest
        serialized = manifest["model"].get("serializedFile")
        if not serialized:
            raise RuntimeError("manifest.model.serializedFile 缺失")
        model_path = os.path.join(model_dir, serialized)

        self.model = YOLO(model_path) 
        # 类别名
        self.names = list(self.model.names.values()) if isinstance(self.model.names, dict) else self.model.names
        self.initialized = True

    @torch.inference_mode()
    def predict(self, data, context):
        if data is None or (isinstance(data, list) and len(data) == 0):
            return []

        imgs: List[np.ndarray] = []
        imgsz = self.default_imgsz
        conf  = self.default_conf
        iou   = self.default_iou

        for it in data:
            img_bytes, ov = _extract_image_bytes(it)
            if ov:
                if ov.get("imgsz") is not None:
                    try: imgsz = int(ov["imgsz"])
                    except: pass
                if ov.get("conf") is not None:
                    try: conf = float(ov["conf"])
                    except: pass
                if ov.get("iou") is not None:
                    try: iou = float(ov["iou"])
                    except: pass
            if img_bytes is None:
                continue
            im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            imgs.append(np.array(im))

        if not imgs:
            return [{"error": "no image in request"}]

        dev = 0 if self.device.type == "cuda" else "cpu"
        results = self.model.predict(
            source=imgs,
            imgsz=imgsz,
            conf=conf,
            iou=iou,
            device=dev,
            verbose=False,
        )

        outs: List[List[Dict[str, Any]]] = []
        names = self.names or []
        for r in results:
            dets: List[Dict[str, Any]] = []
            if getattr(r, "boxes", None) is not None:
                b = r.boxes
                xyxy = b.xyxy.cpu().numpy() if hasattr(b, "xyxy") else None
                scores = b.conf.cpu().numpy() if hasattr(b, "conf") else None
                clses  = b.cls.cpu().numpy().astype(int) if hasattr(b, "cls") else None
                if xyxy is not None and scores is not None and clses is not None:
                    for (x1, y1, x2, y2), sc, cid in zip(xyxy, scores, clses):
                        name = names[cid] if names and 0 <= cid < len(names) else str(int(cid))
                        dets.append({
                            "bbox": [float(x1), float(y1), float(x2), float(y2)],
                            "score": float(sc),
                            "class_id": int(cid),
                            "class_name": name,
                        })
            outs.append(dets)
        return outs

_service = _Service()

def handle(data, context):
    if not _service.initialized:
        _service.initialize(context)
    return _service.predict(data, context)

