from pathlib import Path
import json
import tempfile

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageOps

from ml_models.disease_model import get_agronomic_advisory


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = (
    PROJECT_ROOT
    / "disease_detection"
    / "models"
    / "disease_cnn_30_epochs.pth"
)

MAPPING_PATH = PROJECT_ROOT / "disease_detection" / "class_mapping.json"


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# CROP / DISEASE MAPPINGS
# ============================================================

with open(MAPPING_PATH, "r", encoding="utf-8") as mapping_file:
    disease_classes = json.load(mapping_file)

# This order is part of the trained CNN checkpoint.  It is stored with the
# deployment files so prediction does not require the original training data.
crops = list(disease_classes.keys())


crop_to_index = {
    crop: index
    for index, crop in enumerate(crops)
}


disease_to_index = {
    crop: {disease: index for index, disease in enumerate(diseases)}
    for crop, diseases in disease_classes.items()
}

# Names used by the existing website that differ from the dataset folder names.
# This keeps the current UI compatible with the trained model.
CROP_ALIASES = {
    "rice": "paddy_doctor",
    "paddy": "paddy_doctor",
    "corn": "maize",
    "chili": "chilli",
    "pepper": "chilli",
}


index_to_disease = {
    crop: {
        index: disease
        for disease, index in disease_mapping.items()
    }
    for crop, disease_mapping in disease_to_index.items()
}


# ============================================================
# CNN BLOCK
# ============================================================

class ConvBlock(nn.Module):

    def __init__(self, in_channel, out_channel):

        super().__init__()

        self.block = nn.Sequential(

            nn.Conv2d(
                in_channels=in_channel,
                out_channels=out_channel,
                kernel_size=3,
                padding=1
            ),

            nn.BatchNorm2d(out_channel),

            nn.ReLU(),

            nn.MaxPool2d(
                kernel_size=2
            )
        )


    def forward(self, x):

        return self.block(x)


# ============================================================
# CNN MODEL
# ============================================================

class BaselineCNN(nn.Module):

    def __init__(self, crops, disease_to_index):

        super().__init__()

        self.features = nn.Sequential(

            ConvBlock(3, 64),

            ConvBlock(64, 128),

            ConvBlock(128, 256),

            ConvBlock(256, 512),

            nn.AdaptiveAvgPool2d((1, 1))
        )


        self.classifier = nn.Sequential(

            nn.Flatten(),

            nn.Linear(512, 512),

            nn.ReLU(),

            nn.Dropout(0.5)
        )


        self.disease_heads = nn.ModuleList(

            [
                nn.Linear(
                    512,
                    len(disease_to_index[crop])
                )

                for crop in crops
            ]
        )


    def forward(self, x, crop_labels):

        x = self.features(x)

        x = self.classifier(x)

        outputs = [None] * len(self.disease_heads)


        for crop_index in torch.unique(crop_labels):

            crop_index = crop_index.item()

            mask = crop_labels == crop_index

            crop_features = x[mask]

            crop_output = self.disease_heads[crop_index](
                crop_features
            )

            outputs[crop_index] = crop_output


        return outputs


# ============================================================
# LOAD TRAINED MODEL
# ============================================================

_model = None


def get_model():
    """Load the trained checkpoint only when a disease analysis is requested."""
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"CNN weights not found: {MODEL_PATH}")
        _model = BaselineCNN(crops, disease_to_index)
        _model.load_state_dict(
            torch.load(MODEL_PATH, map_location=device, weights_only=True)
        )
        _model.to(device)
        _model.eval()
    return _model


# ============================================================
# SINGLE IMAGE PREDICTION
# ============================================================

def predict_image(image_path, crop_name):
    """
    Predict the disease for one image when the crop is known.

    Returns:
        crop
        disease
        confidence
    """

    image_path = Path(image_path)


    if not image_path.exists():

        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )


    crop_name = CROP_ALIASES.get(crop_name.strip().lower(), crop_name.strip().lower())


    if crop_name not in crop_to_index:

        raise ValueError(
            f"Unknown crop '{crop_name}'. "
            f"Supported crops: {crops}"
        )


    # --------------------------------------------------------
    # Load image
    # --------------------------------------------------------

    image = Image.open(
        image_path
    ).convert("RGB")


    # --------------------------------------------------------
    # EXACT TRAINING / EVALUATION PREPROCESSING
    # --------------------------------------------------------

    image = ImageOps.pad(
        image,
        (128, 128),
        color=(0, 0, 0)
    )


    image = torch.from_numpy(
        np.array(
            image,
            dtype=np.uint8
        )
    ).permute(
        2,
        0,
        1
    ).float() / 255.0


    # Add batch dimension

    image = image.unsqueeze(0).to(device)


    # --------------------------------------------------------
    # Crop label
    # --------------------------------------------------------

    crop_label = torch.tensor(
        [crop_to_index[crop_name]],
        dtype=torch.long,
        device=device
    )


    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    with torch.inference_mode():

        outputs = get_model()(
            image,
            crop_label
        )


        logits = outputs[
            crop_to_index[crop_name]
        ]


        probabilities = torch.softmax(
            logits,
            dim=1
        )[0]


        confidence, prediction_index = probabilities.max(
            dim=0
        )


    prediction_index = prediction_index.item()

    confidence = confidence.item()


    disease_name = index_to_disease[
        crop_name
    ][prediction_index]


    return {
        "crop": crop_name,
        "disease": disease_name,
        "confidence": round(
            confidence * 100,
            2
        )
    }


# ============================================================
# FLASK / APPLICATION PREDICTION
# ============================================================

def predict_uploaded_image(image_bytes, crop_name):
    """
    Predict disease from uploaded image bytes.

    This function connects the new CNN to the existing
    agronomic advisory system.

    Returns the exact result structure expected by
    the existing disease-detection frontend.
    """

    crop_name = crop_name.strip().lower()


    if crop_name not in crop_to_index:

        raise ValueError(
            f"Unsupported crop '{crop_name}'. "
            f"Supported crops: {crops}"
        )


    temp_path = None


    try:

        # ----------------------------------------------------
        # Temporarily save uploaded image
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
            delete=False
        ) as temp_file:

            temp_file.write(image_bytes)

            temp_path = Path(
                temp_file.name
            )


        # ----------------------------------------------------
        # Run the new CNN
        # ----------------------------------------------------

        prediction = predict_image(
            temp_path,
            crop_name
        )


        # ----------------------------------------------------
        # Connect CNN prediction to existing advisory system
        #
        # Example:
        #
        # tomato + Late_Blight
        #        ↓
        # tomato_Late_Blight
        #        ↓
        # get_agronomic_advisory()
        # ----------------------------------------------------

        class_name = (
            f"{prediction['crop']}_{prediction['disease']}"
        )


        advisory = get_agronomic_advisory(
            class_name
        )


        # ----------------------------------------------------
        # Return frontend-compatible result
        # ----------------------------------------------------

        return {

            "disease_name": advisory["disease_name"],

            "plant_type": advisory["plant_type"],

            "severity": advisory["severity"],

            "confidence": prediction["confidence"],

            "symptoms": advisory["symptoms"],

            "treatment": advisory["treatment"],

            "medicine": advisory["medicine"],

            "organic_solution": advisory["organic_solution"],

            "preventive_measures": advisory[
                "preventive_measures"
            ],

            "is_healthy": (
                prediction["disease"].lower()
                == "healthy"
            )
        }


    finally:

        # ----------------------------------------------------
        # Delete temporary image
        # ----------------------------------------------------

        if (
            temp_path is not None
            and temp_path.exists()
        ):

            temp_path.unlink()
