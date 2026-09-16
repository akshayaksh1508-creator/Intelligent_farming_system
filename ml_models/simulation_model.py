"""
Farm Wise AI – Stage 1 Crop Simulator ML Prediction Service
Inference pipeline for Virtual Farm / Crop Simulator 3D.
Trained on prototype/synthetic agricultural data.
"""

from pathlib import Path
import json
import logging
import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
MODEL_BUNDLE_PATH = BASE_DIR / "simulation_results_models.joblib"
SCHEMA_PATH = BASE_DIR / "simulation_results_schema.json"
METRICS_PATH = BASE_DIR / "simulation_results_metrics.json"

# Configurable prototype market prices (INR per tonne)
# Easily replaceable with real live APMC/mandi prices later
CROP_PRICES_PER_TONNE = {
    "Rice": 22000,
    "Wheat": 22750,
    "Maize": 3035,      # Calibrated for prototype simulation UI
    "Tomato": 2500,     # Calibrated for high-yield horticulture
    "Cotton": 66200,
    "Sugarcane": 3500,
    "Soybean": 46000,
    "Groundnut": 58500,
    "Banana": 2500
}

# Agronomic optimal and tolerance ranges for suitability breakdown
AGRONOMIC_RANGES = {
    "Rice": {
        "temp": ((22, 32), (15, 42)), "moist": ((65, 85), (40, 95)),
        "ph": ((5.5, 7.0), (4.5, 8.5)), "rain": ((1100, 1800), (500, 3000)),
        "n": ((80, 130), (30, 200)), "potential_yield": 5.2
    },
    "Wheat": {
        "temp": ((14, 24), (8, 35)), "moist": ((45, 65), (25, 85)),
        "ph": ((6.0, 7.5), (5.0, 8.8)), "rain": ((400, 750), (150, 1500)),
        "n": ((90, 140), (30, 200)), "potential_yield": 4.8
    },
    "Maize": {
        "temp": ((18, 30), (10, 40)), "moist": ((45, 65), (20, 85)),
        "ph": ((5.8, 7.2), (4.8, 8.5)), "rain": ((550, 850), (200, 1800)),
        "n": ((70, 130), (25, 200)), "potential_yield": 5.8
    },
    "Tomato": {
        "temp": ((18, 28), (10, 38)), "moist": ((50, 70), (25, 90)),
        "ph": ((6.0, 7.0), (5.0, 8.2)), "rain": ((450, 750), (150, 1600)),
        "n": ((80, 140), (25, 200)), "potential_yield": 32.0
    },
    "Cotton": {
        "temp": ((24, 36), (16, 44)), "moist": ((40, 60), (20, 80)),
        "ph": ((6.2, 8.0), (5.2, 8.8)), "rain": ((550, 900), (250, 1800)),
        "n": ((90, 150), (30, 200)), "potential_yield": 3.0
    },
    "Sugarcane": {
        "temp": ((22, 36), (15, 45)), "moist": ((65, 85), (35, 95)),
        "ph": ((6.0, 7.6), (5.0, 8.6)), "rain": ((1300, 2200), (600, 3200)),
        "n": ((140, 220), (50, 250)), "potential_yield": 88.0
    },
    "Soybean": {
        "temp": ((20, 32), (12, 40)), "moist": ((50, 70), (25, 85)),
        "ph": ((6.0, 7.2), (5.0, 8.5)), "rain": ((500, 850), (200, 1600)),
        "n": ((30, 70), (10, 160)), "potential_yield": 3.4
    },
    "Groundnut": {
        "temp": ((22, 34), (14, 42)), "moist": ((45, 65), (20, 85)),
        "ph": ((5.8, 7.2), (4.8, 8.5)), "rain": ((450, 750), (200, 1500)),
        "n": ((25, 60), (10, 150)), "potential_yield": 3.1
    },
    "Banana": {
        "temp": ((22, 36), (14, 44)), "moist": ((60, 80), (35, 95)),
        "ph": ((5.8, 7.2), (4.8, 8.4)), "rain": ((1100, 1900), (500, 3000)),
        "n": ((120, 190), (40, 240)), "potential_yield": 45.0
    }
}

_bundle = None

def get_simulation_model():
    """Load and cache the trained simulation models bundle."""
    global _bundle
    if _bundle is None:
        if not MODEL_BUNDLE_PATH.exists():
            raise FileNotFoundError(
                f"Trained simulation model bundle not found at {MODEL_BUNDLE_PATH}. "
                "Please run `python ml_models/train_simulation_model.py` to train it."
            )
        _bundle = joblib.load(MODEL_BUNDLE_PATH)
        logger.info("Loaded Stage 1 simulation model bundle successfully.")
    return _bundle

def compute_suitability_fit(value, opt_range, tol_range):
    """Calculate 0-100% suitability fit for an environmental variable."""
    omin, omax = opt_range
    tmin, tmax = tol_range
    if omin <= value <= omax:
        return 100
    elif value < omin:
        if value <= tmin:
            return 5
        score = 5 + 95 * ((value - tmin) / max(0.001, (omin - tmin)))
        return int(round(max(5, min(100, score))))
    else:
        if value >= tmax:
            return 5
        score = 5 + 95 * ((tmax - value) / max(0.001, (tmax - omax)))
        return int(round(max(5, min(100, score))))

def generate_ai_advisory(crop, condition, yield_t_ha, potential_yield, params, agro):
    """Generate dynamic contextual AI advisory based on predicted condition and limiting factors."""
    recs = []
    
    # Soil pH
    ph_opt, _ = agro["ph"]
    if params["ph"] < ph_opt[0]:
        recs.append(f"Soil pH ({params['ph']}) is too acidic - apply agricultural lime to raise pH to {ph_opt[0]}+.")
    elif params["ph"] > ph_opt[1]:
        recs.append(f"Soil pH ({params['ph']}) is alkaline - apply gypsum or organic compost to lower pH.")

    # Soil moisture
    m_opt, _ = agro["moist"]
    if params["moist"] < m_opt[0]:
        recs.append(f"Soil moisture ({params['moist']}%) is below optimal - supplement with drip or sprinkler irrigation.")
    elif params["moist"] > m_opt[1]:
        recs.append(f"Soil moisture ({params['moist']}%) is high - ensure proper furrow drainage to prevent root rot.")

    # Temperature
    t_opt, _ = agro["temp"]
    if params["temp"] > t_opt[1]:
        recs.append(f"Temperature ({params['temp']}°C) exceeds heat threshold - consider shade nets or mulching.")
    elif params["temp"] < t_opt[0]:
        recs.append(f"Temperature ({params['temp']}°C) is cold for {crop} - consider delayed sowing or polytunnel covers.")

    # Rainfall
    r_opt, _ = agro["rain"]
    if params["rain"] < r_opt[0]:
        recs.append(f"Rainfall ({params['rain']} mm) is deficient for full growth - schedule supplemental watering.")

    # Nitrogen
    n_opt, _ = agro["n"]
    if params["n"] < n_opt[0]:
        recs.append(f"Nitrogen ({params['n']} kg) is deficient - apply urea or neem-coated nitrogenous fertilizer.")

    limiting_text = " ".join(recs[:2]) if recs else "All core soil and climate parameters are well balanced."

    if condition == "Good":
        advisory = (
            f"{crop} - Conditions are good! Predicted yield of {yield_t_ha:.2f} t/ha is strong and on track. "
            f"{limiting_text} Maintain current irrigation and pest management for a peak harvest."
        )
    elif condition == "Moderate":
        advisory = (
            f"{crop} - Conditions are moderate. With improvements, yield can increase to {potential_yield:.2f} t/ha. "
            f"{limiting_text}"
        )
    else:
        advisory = (
            f"{crop} - Conditions are poor. High risk of suppressed crop performance. "
            f"{limiting_text} Consider intensive soil amendments before planting."
        )
    return advisory

def predict_simulation(data: dict) -> dict:
    """
    Main prediction pipeline for Crop Simulator 3D.
    Accepts input dictionary and outputs predicted simulation metrics and condition breakdown.
    """
    bundle = get_simulation_model()
    
    # 1. Parse and validate inputs
    crop_raw = str(data.get("crop", "Maize")).strip()
    crop_canonical = crop_raw.capitalize()
    if crop_canonical not in CROP_PRICES_PER_TONNE:
        # Match case-insensitive
        matches = [c for c in CROP_PRICES_PER_TONNE if c.lower() == crop_raw.lower()]
        crop_canonical = matches[0] if matches else "Maize"

    area_ha = float(data.get("area_ha", 1.0))
    area_ha = max(0.1, min(100.0, area_ha))

    temp = float(data.get("temperature", data.get("temperature_c", data.get("temp", 24.0))))
    moist = float(data.get("soil_moisture", data.get("soil_moisture_pct", data.get("moist", 50.0))))
    ph = float(data.get("soil_ph", data.get("ph", 6.5)))
    rain = float(data.get("annual_rainfall", data.get("rainfall_mm", data.get("rainfall", data.get("rain", 700.0)))))
    n = float(data.get("nitrogen", data.get("nitrogen_kg_ha", data.get("n", 70.0))))

    fert = float(data.get("fertilizer_level", data.get("fertilizer", 60.0)))
    irrig = float(data.get("irrigation_level", data.get("irrigation", 50.0)))

    # 2. Compute Condition Breakdown Fits (0-100%)
    agro = AGRONOMIC_RANGES.get(crop_canonical, AGRONOMIC_RANGES["Maize"])
    t_fit = compute_suitability_fit(temp, agro["temp"][0], agro["temp"][1])
    p_fit = compute_suitability_fit(ph, agro["ph"][0], agro["ph"][1])
    m_fit = compute_suitability_fit(moist, agro["moist"][0], agro["moist"][1])
    r_fit = compute_suitability_fit(rain, agro["rain"][0], agro["rain"][1])
    n_fit = compute_suitability_fit(n, agro["n"][0], agro["n"][1])

    # 3. Model Inference
    num_features = bundle["num_features"]
    feature_row = pd.DataFrame([{
        "area_ha": area_ha,
        "temperature": temp,
        "soil_moisture": moist,
        "soil_ph": ph,
        "annual_rainfall": rain,
        "nitrogen": n,
        "fertilizer_level": fert,
        "irrigation_level": irrig
    }])[num_features]

    if crop_canonical in bundle.get("crop_models", {}):
        crop_mod = bundle["crop_models"][crop_canonical]
        reg_preds = crop_mod["regressor"].predict(feature_row)[0]
        cond_pred = crop_mod["classifier"].predict(feature_row)[0]
    else:
        # Fallback to unified global model
        global_features = bundle["global_features"]
        full_row = {f: 0.0 for f in global_features}
        for nf in num_features:
            full_row[nf] = feature_row[nf].iloc[0]
        crop_col = f"crop_{crop_canonical}"
        if crop_col in full_row:
            full_row[crop_col] = 1.0
        g_df = pd.DataFrame([full_row])[global_features]
        reg_preds = bundle["global_reg"].predict(g_df)[0]
        cond_pred = bundle["global_clf"].predict(g_df)[0]

    # Map regression outputs
    reg_targets = bundle["reg_target_cols"]
    raw_results = dict(zip(reg_targets, reg_preds))

    yield_t_ha = round(max(0.1, float(raw_results["yield_t_ha"])), 2)
    water_mm = int(round(max(50, float(raw_results["water_mm"]))))
    harvest_days = int(round(max(40, float(raw_results["harvest_days"]))))
    co2_credits = round(max(0.1, float(raw_results["co2_credits"])), 1)
    input_cost = int(round(max(500, float(raw_results["input_cost"]))))
    success_rate = int(round(max(5, min(99, float(raw_results["success_rate"])))))
    condition = str(cond_pred)

    # 4. Derived calculations
    price_per_tonne = CROP_PRICES_PER_TONNE.get(crop_canonical, 3000)
    season_income = int(round(yield_t_ha * area_ha * price_per_tonne))
    net_roi = int(round(((season_income - input_cost) / input_cost) * 100)) if input_cost > 0 else 0

    # 5. Generate dynamic AI Advisory
    potential_yield = agro.get("potential_yield", yield_t_ha * 1.25)
    params_dict = {"ph": ph, "moist": moist, "temp": temp, "rain": rain, "n": n}
    advisory = generate_ai_advisory(crop_canonical, condition, yield_t_ha, potential_yield, params_dict, agro)

    return {
        "season_income": season_income,
        "yield_t_ha": yield_t_ha,
        "success_rate": success_rate,
        "water_mm": water_mm,
        "harvest_days": harvest_days,
        "co2_credits": co2_credits,
        "input_cost": input_cost,
        "net_roi": net_roi,
        "condition": condition,
        "advisory": advisory,
        "temperature_fit": t_fit,
        "ph_fit": p_fit,
        "moisture_fit": m_fit,
        "rainfall_fit": r_fit,
        "nitrogen_fit": n_fit,
        "crop": crop_canonical,
        "area_ha": area_ha,
        "price_per_tonne": price_per_tonne,
        "is_synthetic_prototype": True
    }
