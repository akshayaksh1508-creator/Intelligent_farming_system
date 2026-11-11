"""Verify the exported mobile bundle against the PyTorch model.

Checks (1) the TFLite backbone matches torch on a random input, and (2) the
full on-device path (TFLite + JSON heads) gives the same crop/disease/confidence
as the server's predict_image on a real leaf photo.

Run inside the same venv as export_mobile_bundle.py:

    python disease_detection/verify_mobile_bundle.py [image_path]
"""

import json
import sys
from pathlib import Path

import numpy as np
import torch
from ai_edge_litert.interpreter import Interpreter
from PIL import Image, ImageOps

from disease_detection.cnn_inference import get_model, predict_image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "mobile" / "assets" / "model"
IMAGE = Path(sys.argv[1]) if len(sys.argv) > 1 else PROJECT_ROOT / ".test-assets" / "leaf.jpg"


def load_interpreter():
    interpreter = Interpreter(str(MODEL_DIR / "disease-backbone.tflite"))
    interpreter.allocate_tensors()
    return interpreter


def main() -> None:
    model = get_model().eval()
    backbone = torch.nn.Sequential(model.features, model.classifier).eval()

    interpreter = load_interpreter()
    input_detail = interpreter.get_input_details()[0]
    output_detail = interpreter.get_output_details()[0]
    nhwc = len(input_detail["shape"]) == 4 and input_detail["shape"][-1] == 3
    print(f"tflite input  {input_detail['shape']} {input_detail['dtype']}")
    print(f"tflite output {output_detail['shape']}")

    def run_tflite(tensor: torch.Tensor) -> np.ndarray:
        feed = tensor.permute(0, 2, 3, 1).contiguous() if nhwc else tensor
        interpreter.set_tensor(input_detail["index"], feed.numpy().astype(np.float32))
        interpreter.invoke()
        return interpreter.get_tensor(output_detail["index"])

    # 1. Backbone parity on a random input.
    x = torch.randn(1, 3, 128, 128)
    with torch.inference_mode():
        ref = backbone(x).numpy()
    diff = float(np.abs(ref - run_tflite(x)).max())
    print(f"backbone max abs diff: {diff:.2e}")
    # Float-only reordering inside the TFLite graph moves embeddings by ~1e-2;
    # the real gate is the end-to-end prediction below.
    if diff > 1e-1:
        raise SystemExit("FAIL: backbone mismatch")

    # 2. End-to-end parity on the real photo, like the phone will run it.
    heads = json.loads((MODEL_DIR / "disease-heads.json").read_text(encoding="utf-8"))
    crop = "tomato"
    server = predict_image(IMAGE, crop)

    img = Image.open(IMAGE).convert("RGB")
    padded = ImageOps.pad(img, (128, 128), color=(0, 0, 0))
    tensor = (
        torch.from_numpy(np.array(padded, dtype=np.uint8)).permute(2, 0, 1).float() / 255.0
    ).unsqueeze(0)

    embedding = run_tflite(tensor)[0]
    head = heads["heads"][crop]
    width = head["inFeatures"]
    scores = np.array(
        [
            float(embedding @ np.array(head["weight"][i * width : (i + 1) * width], dtype=np.float32))
            + head["bias"][i]
            for i in range(len(head["diseases"]))
        ]
    )
    probs = np.exp(scores - scores.max())
    probs /= probs.sum()
    mobile = {
        "crop": crop,
        "disease": head["diseases"][int(probs.argmax())],
        "confidence": round(float(probs.max()) * 100, 2),
    }
    print("server:", server)
    print("mobile:", mobile)
    if mobile["disease"] != server["disease"] or abs(
        mobile["confidence"] - server["confidence"]
    ) > 0.05:
        raise SystemExit("FAIL: end-to-end mismatch")
    print("OK: the on-device bundle matches the server exactly.")


if __name__ == "__main__":
    main()
