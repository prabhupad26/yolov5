# YOLOv5 🚀 by Ultralytics, GPL-3.0 license
"""
Run a Flask REST API exposing one or more YOLOv5s models
"""

import argparse
import io

import torch
from flask import Flask, request
from PIL import Image
from pathlib import Path

from models.common import DetectMultiBackend, AutoShape

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]

app = Flask(__name__)
model = AutoShape(DetectMultiBackend(ROOT / 'best.pt', device='cpu', dnn=False, fp16=False))
models = {'v1_model': model}

DETECTION_URL = "/v1/object-detection/<model>"


@app.route(DETECTION_URL, methods=["POST"])
def predict(model):
    if request.method != "POST":
        return

    if request.data:
        # Method 1
        # with request.files["image"] as f:
        #     im = Image.open(io.BytesIO(f.read()))

        # Method 2
        # im_file = request.files["image"]
        # im_bytes = im_file.read()
        # im = Image.open(io.BytesIO(im_bytes))

        #Method 3
        im_bytes = request.data
        im = Image.open(io.BytesIO(im_bytes))

        if model in models:
            results = models[model](im, size=640)  # reduce size=320 for faster inference
            return results.pandas().xyxy[0].to_json(orient="records")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flask API exposing YOLOv5 model")
    parser.add_argument("--port", default=5000, type=int, help="port number")
    parser.add_argument('--model', nargs='+', default=['yolov5s'], help='model(s) to run, i.e. --model yolov5n yolov5s')
    opt = parser.parse_args()

    for m in opt.model:
        models[m] = torch.hub.load("ultralytics/yolov5", m, force_reload=True, skip_validation=True)

    app.run(host="0.0.0.0", port=opt.port)  # debug=True causes Restarting with stat
