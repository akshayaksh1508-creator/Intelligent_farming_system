"""Build the on-device disease bundle for the Farm Wise mobile app.

Exports the trained CNN's backbone (features + 512-d classifier) to TFLite and
writes the per-crop disease heads and the agronomic advisory texts as JSON, so
the phone runs the exact same prediction as /api/disease/analyze — no server.

The CNN (BaselineCNN) routes each crop through its own 512->N linear head, so
the full graph cannot be exported statically. The mobile app runs the shared
backbone on-device and applies the selected crop's head in plain TypeScript.

Run inside a venv with torch + ai-edge-torch + ai-edge-litert:

    python disease_detection/export_mobile_bundle.py

Outputs (overwrites): mobile/assets/model/disease-backbone.tflite,
mobile/assets/model/disease-heads.json, mobile/assets/model/disease-advisory.json
"""

import json
from pathlib import Path

import torch

from disease_detection.cnn_inference import CROP_ALIASES, BaselineCNN, crops, disease_to_index, get_model
from ml_models.disease_model import get_agronomic_advisory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MOBILE_MODEL_DIR = PROJECT_ROOT / "mobile" / "assets" / "model"


def export_backbone_tflite(model: BaselineCNN, path: Path) -> None:
    # ai-edge-torch needs torch-xla, which has no Windows wheels — so the
    # conversion goes torch -> ONNX -> onnx2tf -> TFLite instead.
    import onnx
    import onnx2tf
    import onnx2tf.onnx2tf as onnx2tf_module
    import numpy as np

    # onnx2tf downloads a pickled sample .npy for output checking (unused here);
    # numpy refuses to load it, so feed it local dummy data instead.
    onnx2tf_module.download_test_image_data = lambda: np.zeros(
        (1, 128, 128, 3), dtype=np.float32
    )

    # Dropout is identity in eval mode, so features + classifier is the whole
    # shared computation; the per-crop heads come from the JSON below.
    backbone = torch.nn.Sequential(model.features, model.classifier).eval()
    onnx_path = path.with_suffix(".onnx")
    torch.onnx.export(
        backbone,
        (torch.randn(1, 3, 128, 128),),
        str(onnx_path),
        opset_version=17,
        input_names=["input"],
        output_names=["embedding"],
    )
    out_dir = path.parent / "onnx2tf-out"
    onnx2tf.convert(
        input_onnx_file_path=str(onnx_path),
        output_folder_path=str(out_dir),
        non_verbose=True,
    )
    tflite_files = list(out_dir.glob("*.tflite"))
    if not tflite_files:
        raise RuntimeError("onnx2tf produced no .tflite file")
    tflite_files[0].replace(path)
    onnx_path.unlink()
    import shutil

    shutil.rmtree(out_dir, ignore_errors=True)
    print(f"wrote {path}")


def export_heads_json(model: BaselineCNN, path: Path) -> None:
    heads = {
        crop: {
            "index": index,
            "diseases": list(disease_to_index[crop].keys()),
            "weight": model.disease_heads[index].weight.detach().cpu().flatten().tolist(),
            "bias": model.disease_heads[index].bias.detach().cpu().tolist(),
            "inFeatures": model.disease_heads[index].weight.shape[1],
        }
        for index, crop in enumerate(crops)
    }
    path.write_text(
        json.dumps({"crops": crops, "aliases": CROP_ALIASES, "heads": heads}, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"wrote {path}")


def export_advisory_json(path: Path) -> None:
    advisory = {}
    for crop in crops:
        for disease in disease_to_index[crop]:
            advisory[f"{crop}_{disease}"] = get_agronomic_advisory(f"{crop}_{disease}")
    path.write_text(json.dumps(advisory, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {path}")


def main() -> None:
    model = get_model().eval()
    MOBILE_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    export_backbone_tflite(model, MOBILE_MODEL_DIR / "disease-backbone.tflite")
    export_heads_json(model, MOBILE_MODEL_DIR / "disease-heads.json")
    export_advisory_json(MOBILE_MODEL_DIR / "disease-advisory.json")


if __name__ == "__main__":
    main()
