# ============================================================
# Farm Wise AI – Gemini Vision Disease Detection Service
# Uses Google Gemini Vision API to analyze plant leaf images
# with expert-level agricultural knowledge.
# Falls back to local CNN model if API key is not configured.
# ============================================================

import os
import io
import json
from pathlib import Path


# ── Gemini API configuration ──────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Expert prompt for disease detection
DISEASE_EXPERT_PROMPT = """You are an expert plant pathologist and agricultural scientist with deep knowledge of crop diseases.

Analyze this leaf image carefully and provide a structured disease diagnosis.

IMPORTANT INSTRUCTIONS:
1. Look for disease symptoms: spots, lesions, discoloration, wilting, pustules, mold, blight, rot, mosaic patterns
2. Identify the specific disease name (not just "diseased" — give the exact disease)
3. Assess severity based on what fraction of the leaf is affected
4. Provide ICAR-approved treatment recommendations
5. If the leaf is GENUINELY healthy with NO visible symptoms, only then say Healthy

Respond ONLY with a valid JSON object in this exact format (no markdown, no extra text):
{
  "disease_name": "Tomato Bacterial Spot",
  "plant_type": "Tomato",
  "severity": "High",
  "confidence": 92,
  "is_healthy": false,
  "symptoms": "Small dark brown water-soaked spots with yellow halos on leaves. Angular lesions along veins.",
  "treatment": "Spray Streptocycline 0.5g/10L + Copper Oxychloride 2.5g/L. Repeat every 7 days.",
  "medicine": "Streptocycline, Blitox 50, Copper Oxychloride 50WP",
  "organic_solution": "Spray Copper Hydroxide or Bordeaux mixture (1%) weekly. Remove infected leaves.",
  "preventive_measures": "Use certified disease-free seeds, avoid overhead irrigation, practice crop rotation.",
  "diagnosis_source": "gemini_vision"
}

Severity must be one of: None, Low, Moderate, High, Very High
confidence must be an integer 0-99
is_healthy must be true only if there are absolutely NO disease symptoms
"""


def analyze_with_gemini(image_bytes: bytes, plant_type: str = "Unknown") -> dict | None:
    """
    Sends a leaf image to Google Gemini Vision API for disease diagnosis.
    Returns a result dict matching the disease_model.predict() format,
    or None if the API call fails.
    """
    if not GEMINI_API_KEY:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)

        # Build the prompt with plant type hint
        prompt = DISEASE_EXPERT_PROMPT
        if plant_type and plant_type.lower() not in ("unknown", ""):
            prompt = f"The farmer indicates this is a {plant_type} plant.\n\n" + prompt

        # Prepare image part
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=_detect_mime_type(image_bytes)
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, image_part]
        )
        raw_text = response.text.strip()

        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        result = json.loads(raw_text.strip())

        # Validate required fields
        required = ["disease_name", "plant_type", "severity", "confidence", "is_healthy",
                    "symptoms", "treatment", "medicine", "organic_solution", "preventive_measures"]
        for key in required:
            if key not in result:
                raise ValueError(f"Missing key in Gemini response: {key}")

        # Normalize types
        result["confidence"] = float(result.get("confidence", 80))
        result["is_healthy"] = bool(result.get("is_healthy", False))
        result["diagnosis_source"] = "gemini_vision"

        # Honour farmer's plant type selection
        if plant_type and plant_type.lower() not in ("unknown", ""):
            result["plant_type"] = plant_type

        print(f"[Gemini Vision] Detected: {result['disease_name']} "
              f"({result['confidence']}% confidence)")
        return result

    except json.JSONDecodeError as e:
        print(f"[Gemini Vision] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"[Gemini Vision] API error: {e}")
        return None



def _detect_mime_type(image_bytes: bytes) -> str:
    """Detect image MIME type from magic bytes."""
    if image_bytes[:3] == b'\xff\xd8\xff':
        return "image/jpeg"
    elif image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return "image/png"
    elif image_bytes[:4] == b'RIFF':
        return "image/webp"
    elif image_bytes[:6] in (b'GIF87a', b'GIF89a'):
        return "image/gif"
    return "image/jpeg"  # default fallback


def is_gemini_available() -> bool:
    """Returns True if the Gemini API key is configured."""
    return bool(GEMINI_API_KEY)
