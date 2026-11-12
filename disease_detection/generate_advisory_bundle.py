"""
Regenerates mobile/assets/model/disease-advisory.json with real, AI-researched
treatment information for every disease class in the CNN, so the mobile app's
on-device results show accurate info too.

Requires GEMINI_API_KEY (free at https://aistudio.google.com/apikey).

Usage (PowerShell):
    $env:GEMINI_API_KEY = "your-key-here"
    python disease_detection/generate_advisory_bundle.py
"""

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml_models.gemini_disease_service import GEMINI_API_KEY, generate_disease_advisory

MAPPING_PATH = PROJECT_ROOT / "disease_detection" / "class_mapping.json"
ADVISORY_PATH = PROJECT_ROOT / "mobile" / "assets" / "model" / "disease-advisory.json"

SLEEP_SECONDS = 4.5  # stay under the Gemini free tier (15 requests/minute)

ADVISORY_KEYS = (
    "disease_name",
    "plant_type",
    "severity",
    "symptoms",
    "treatment",
    "medicine",
    "organic_solution",
    "preventive_measures",
)


def main():
    if not GEMINI_API_KEY:
        print("Set GEMINI_API_KEY first (free at https://aistudio.google.com/apikey).")
        sys.exit(1)

    mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    advisory = json.loads(ADVISORY_PATH.read_text(encoding="utf-8"))

    total = 0
    updated = 0
    for crop, diseases in mapping.items():
        for disease in diseases:
            if disease.lower() == "healthy":
                continue
            key = f"{crop}_{disease}"
            total += 1
            if key not in advisory:
                print(f"Missing baseline entry for {key}; skipping.")
                continue
            result = generate_disease_advisory(key, 85.0)
            if result is None:
                print(f"[{key}] AI unavailable - kept existing text.")
            else:
                advisory[key] = {k: result[k] for k in ADVISORY_KEYS}
                updated += 1
                print(f"[{key}] -> {result['disease_name']}")
            time.sleep(SLEEP_SECONDS)

    ADVISORY_PATH.write_text(json.dumps(advisory, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Done: {updated}/{total} entries updated in {ADVISORY_PATH}.")


if __name__ == "__main__":
    main()
