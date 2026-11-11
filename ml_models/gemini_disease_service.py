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



# ── AI-generated treatment information for CNN-detected diseases ────────
# The CNN decides *what* the disease is; Gemini writes *real* treatment
# information for that exact disease (accurate dosages, Indian product
# names, organic remedies) instead of the generic keyword templates.

ADVISORY_PROMPT = """You are an expert plant pathologist and agricultural scientist with deep knowledge of Indian crop diseases.

A computer-vision CNN has just classified a leaf photo as: {disease} on {crop} (confidence {confidence}%).

Provide accurate, evidence-based, ICAR-recommended information for this exact disease. Use specific product names and dosages that are available in India.

Respond ONLY with a valid JSON object in this exact format (no markdown, no extra text):
{{
  "disease_name": "Proper human-readable disease name",
  "plant_type": "Crop name",
  "severity": "One of: Low, Moderate, High, Very High",
  "symptoms": "2-3 sentences of the specific visible symptoms",
  "treatment": "Specific chemical treatment with dosage and spray interval",
  "medicine": "Commercial product names available in India, comma separated",
  "organic_solution": "Practical organic or bio-control remedy with dosage",
  "preventive_measures": "Specific prevention practices for this disease"
}}
"""

CROP_DISPLAY_NAMES = {
    "paddy_doctor": "Rice (Paddy)",
    "maize": "Maize (Corn)",
    "chilli": "Chilli",
    "pigeon_pea": "Pigeon Pea",
}

_advisory_cache = {}


def generate_disease_advisory(class_name: str, confidence: float) -> dict | None:
    """
    Generates real, AI-researched treatment information for a CNN-detected disease.

    Returns a dict matching the get_agronomic_advisory() format, or None when
    no API key is configured or the API call fails (the caller then falls back
    to the built-in agronomic database). Results are cached in memory because
    the correct advice for a disease does not change between scans.
    """
    if not GEMINI_API_KEY:
        return None

    cache_key = class_name.strip().lower()
    cached = _advisory_cache.get(cache_key)
    if cached:
        return cached

    parts = class_name.replace("___", "_").split("_")
    crop_key = parts[0].lower() if parts else "plant"
    disease_words = " ".join(
        p for p in parts[1:] if p.lower() != "healthy"
    ).replace("_", " ").title()
    if not disease_words:
        return None

    crop_hint = CROP_DISPLAY_NAMES.get(crop_key, crop_key.replace("_", " ").title())

    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=ADVISORY_PROMPT.format(
                disease=disease_words,
                crop=crop_hint,
                confidence=round(float(confidence), 1),
            ),
        )
        raw_text = (response.text or "").strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        result = json.loads(raw_text.strip())

        required = ["disease_name", "plant_type", "severity", "symptoms",
                    "treatment", "medicine", "organic_solution", "preventive_measures"]
        for key in required:
            if key not in result:
                raise ValueError(f"Missing key in Gemini advisory response: {key}")

        result["diagnosis_source"] = "gemini_advisory"
        _advisory_cache[cache_key] = result
        print(f"[Gemini Advisory] Real treatment info generated for: {result['disease_name']}")
        return result
    except Exception as e:
        print(f"[Gemini Advisory] Skipped ({e}). Using built-in agronomic database.")
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
