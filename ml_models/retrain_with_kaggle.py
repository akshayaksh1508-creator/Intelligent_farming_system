# ============================================================
# Farm Wise AI - Retrain with Kaggle Crop Recommendation Dataset
# Uses REAL sensor data for Rice, Maize, Cotton, Banana
# Uses ICAR/FAO calibrated data for Wheat, Tomato, Sugarcane,
#   Soybean, Groundnut (not in Kaggle)
# ============================================================

import os
import json
import random
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "simulation_data"
KAGGLE_CSV = DATA_DIR / "kaggle_crop_recommendation.csv"
DATASET_PATH = DATA_DIR / "simulation_results_prototype_dataset.csv"
MODEL_BUNDLE_PATH = BASE_DIR / "simulation_results_models.joblib"
SCHEMA_PATH = BASE_DIR / "simulation_results_schema.json"
METRICS_PATH = BASE_DIR / "simulation_results_metrics.json"

# ---- Crop agronomic configuration ----
CROPS_CONFIG = {
    "Rice": {
        "temp_opt": (22, 32), "temp_tol": (15, 42),
        "moist_opt": (65, 85), "moist_tol": (40, 95),
        "ph_opt": (5.5, 7.0), "ph_tol": (4.5, 8.5),
        "rain_opt": (1100, 1800), "rain_tol": (500, 3000),
        "n_opt": (80, 130), "n_tol": (30, 200),
        "p_opt": (30, 60), "k_opt": (30, 60),
        "base_yield": 4.5, "base_water_mm": 1200, "base_days": 120,
        "base_cost_ha": 4800, "price_per_tonne": 22000, "co2_factor": 1.2
    },
    "Wheat": {
        "temp_opt": (14, 24), "temp_tol": (8, 35),
        "moist_opt": (45, 65), "moist_tol": (25, 85),
        "ph_opt": (6.0, 7.5), "ph_tol": (5.0, 8.8),
        "rain_opt": (400, 750), "rain_tol": (150, 1500),
        "n_opt": (90, 140), "n_tol": (30, 200),
        "p_opt": (40, 70), "k_opt": (30, 50),
        "base_yield": 4.0, "base_water_mm": 500, "base_days": 110,
        "base_cost_ha": 4500, "price_per_tonne": 22750, "co2_factor": 1.0
    },
    "Maize": {
        "temp_opt": (18, 30), "temp_tol": (10, 40),
        "moist_opt": (45, 65), "moist_tol": (20, 85),
        "ph_opt": (5.8, 7.2), "ph_tol": (4.8, 8.5),
        "rain_opt": (550, 850), "rain_tol": (200, 1800),
        "n_opt": (70, 130), "n_tol": (25, 200),
        "p_opt": (30, 60), "k_opt": (20, 50),
        "base_yield": 5.1, "base_water_mm": 550, "base_days": 95,
        "base_cost_ha": 4600, "price_per_tonne": 3035, "co2_factor": 1.1
    },
    "Tomato": {
        "temp_opt": (18, 28), "temp_tol": (10, 38),
        "moist_opt": (50, 70), "moist_tol": (25, 90),
        "ph_opt": (6.0, 7.0), "ph_tol": (5.0, 8.2),
        "rain_opt": (450, 750), "rain_tol": (150, 1600),
        "n_opt": (80, 140), "n_tol": (25, 200),
        "p_opt": (40, 80), "k_opt": (40, 70),
        "base_yield": 26.0, "base_water_mm": 600, "base_days": 80,
        "base_cost_ha": 12000, "price_per_tonne": 2500, "co2_factor": 0.8
    },
    "Cotton": {
        "temp_opt": (24, 36), "temp_tol": (16, 44),
        "moist_opt": (40, 60), "moist_tol": (20, 80),
        "ph_opt": (6.2, 8.0), "ph_tol": (5.2, 8.8),
        "rain_opt": (550, 900), "rain_tol": (250, 1800),
        "n_opt": (90, 150), "n_tol": (30, 200),
        "p_opt": (30, 60), "k_opt": (20, 50),
        "base_yield": 2.3, "base_water_mm": 750, "base_days": 175,
        "base_cost_ha": 7500, "price_per_tonne": 66200, "co2_factor": 0.9
    },
    "Sugarcane": {
        "temp_opt": (22, 36), "temp_tol": (15, 45),
        "moist_opt": (65, 85), "moist_tol": (35, 95),
        "ph_opt": (6.0, 7.6), "ph_tol": (5.0, 8.6),
        "rain_opt": (1300, 2200), "rain_tol": (600, 3200),
        "n_opt": (140, 220), "n_tol": (50, 250),
        "p_opt": (50, 90), "k_opt": (50, 80),
        "base_yield": 75.0, "base_water_mm": 1800, "base_days": 330,
        "base_cost_ha": 15000, "price_per_tonne": 3500, "co2_factor": 2.5
    },
    "Soybean": {
        "temp_opt": (20, 32), "temp_tol": (12, 40),
        "moist_opt": (50, 70), "moist_tol": (25, 85),
        "ph_opt": (6.0, 7.2), "ph_tol": (5.0, 8.5),
        "rain_opt": (500, 850), "rain_tol": (200, 1600),
        "n_opt": (30, 70), "n_tol": (10, 160),
        "p_opt": (30, 60), "k_opt": (20, 50),
        "base_yield": 2.8, "base_water_mm": 500, "base_days": 100,
        "base_cost_ha": 4200, "price_per_tonne": 46000, "co2_factor": 1.4
    },
    "Groundnut": {
        "temp_opt": (22, 34), "temp_tol": (14, 42),
        "moist_opt": (45, 65), "moist_tol": (20, 85),
        "ph_opt": (5.8, 7.2), "ph_tol": (4.8, 8.5),
        "rain_opt": (450, 750), "rain_tol": (200, 1500),
        "n_opt": (25, 60), "n_tol": (10, 150),
        "p_opt": (30, 60), "k_opt": (20, 50),
        "base_yield": 2.5, "base_water_mm": 480, "base_days": 115,
        "base_cost_ha": 4800, "price_per_tonne": 58500, "co2_factor": 1.0
    },
    "Banana": {
        "temp_opt": (22, 36), "temp_tol": (14, 44),
        "moist_opt": (60, 80), "moist_tol": (35, 95),
        "ph_opt": (5.8, 7.2), "ph_tol": (4.8, 8.4),
        "rain_opt": (1100, 1900), "rain_tol": (500, 3000),
        "n_opt": (120, 190), "n_tol": (40, 240),
        "p_opt": (30, 70), "k_opt": (40, 80),
        "base_yield": 36.0, "base_water_mm": 1400, "base_days": 270,
        "base_cost_ha": 14000, "price_per_tonne": 2500, "co2_factor": 1.8
    }
}

# Kaggle dataset crop name -> our crop name
KAGGLE_CROP_MAP = {
    "rice": "Rice",
    "maize": "Maize",
    "cotton": "Cotton",
    "banana": "Banana"
}

AREA_HA_CHOICES = [0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.25, 7.5, 10.0, 12.25, 16.0]


def calc_fit(val, opt_range, tol_range):
    """Calculate suitability fit (0.05 to 1.0) for an environmental variable."""
    omin, omax = opt_range
    tmin, tmax = tol_range
    if omin <= val <= omax:
        return 1.0
    elif val < omin:
        if val <= tmin:
            return 0.05
        return 0.05 + 0.95 * (val - tmin) / (omin - tmin)
    else:
        if val >= tmax:
            return 0.05
        return 0.05 + 0.95 * (tmax - val) / (tmax - omax)


from sklearn.multioutput import MultiOutputRegressor

# ... inside retrain_with_kaggle.py ...

def compute_row(crop_name, cfg, temp, moist, ph, rain, n, fert, irrig, area_ha, data_source, is_synthetic):
    """Compute a single training row with all targets from input features."""
    t_fit = calc_fit(temp, cfg["temp_opt"], cfg["temp_tol"])
    p_fit = calc_fit(ph, cfg["ph_opt"], cfg["ph_tol"])
    m_fit = calc_fit(moist, cfg["moist_opt"], cfg["moist_tol"])
    r_fit = calc_fit(rain, cfg["rain_opt"], cfg["rain_tol"])
    n_fit = calc_fit(n, cfg["n_opt"], cfg["n_tol"])

    fits = [t_fit, p_fit, m_fit, r_fit, n_fit]
    S = 0.40 * min(fits) + 0.60 * (sum(fits) / len(fits))
    S = max(0.05, min(1.0, S))

    noise_yield = np.random.normal(1.0, 0.015)
    yield_t_ha = round(max(0.15, cfg["base_yield"] * (0.15 + 0.85 * S) * noise_yield), 2)
    success_rate = int(round(max(5, min(99, S * 100 + np.random.normal(0, 1.0)))))

    water_stress_penalty = 1.0 + 0.30 * (1.0 - m_fit)
    water_mm = int(round(cfg["base_water_mm"] * water_stress_penalty * np.random.normal(1.0, 0.015)))

    days_modifier = 1.0 + 0.12 * (1.0 - t_fit)
    harvest_days = int(round(cfg["base_days"] * days_modifier * np.random.normal(1.0, 0.01)))

    co2_credits = round(max(0.1, cfg["co2_factor"] * area_ha * (0.30 + 0.70 * S) * np.random.normal(1.0, 0.015)), 2)

    cost_per_ha = cfg["base_cost_ha"] * (0.85 + 0.20 * (fert / 100.0) + 0.10 * (irrig / 100.0))
    input_cost = int(round(cost_per_ha * area_ha * np.random.normal(1.0, 0.015)))
    input_cost = max(500, input_cost)

    season_income = int(round(yield_t_ha * area_ha * cfg["price_per_tonne"]))
    net_roi = round(((season_income - input_cost) / input_cost) * 100.0, 1)

    if S >= 0.68:
        condition = "Good"
    elif S >= 0.40:
        condition = "Moderate"
    else:
        condition = "Poor"

    return {
        "crop": crop_name,
        "area_ha": round(area_ha, 2),
        "temperature": round(temp, 1),
        "soil_moisture": round(moist, 1),
        "soil_ph": round(ph, 2),
        "annual_rainfall": round(rain, 0),
        "nitrogen": round(n, 1),
        "fertilizer_level": round(fert, 1),
        "irrigation_level": round(irrig, 1),
        "yield_t_ha": yield_t_ha,
        "water_mm": water_mm,
        "harvest_days": harvest_days,
        "co2_credits": co2_credits,
        "input_cost": input_cost,
        "success_rate": success_rate,
        "season_income": season_income,
        "net_roi": net_roi,
        "temperature_fit": int(round(t_fit * 100)),
        "ph_fit": int(round(p_fit * 100)),
        "moisture_fit": int(round(m_fit * 100)),
        "rainfall_fit": int(round(r_fit * 100)),
        "nitrogen_fit": int(round(n_fit * 100)),
        "condition": condition,
        "data_source": data_source,
        "is_synthetic": is_synthetic,
    }


KAGGLE_RAIN_MULTIPLIERS = {
    "rice": 6.0,
    "maize": 8.0,
    "cotton": 9.0,
    "banana": 13.0
}


def load_kaggle_rows():
    """Load Kaggle CSV and convert to our feature space for matching crops."""
    print(f"Loading Kaggle dataset from {KAGGLE_CSV} ...")
    kaggle_df = pd.read_csv(KAGGLE_CSV)
    print(f"  Loaded {len(kaggle_df)} rows, columns: {list(kaggle_df.columns)}")

    rows = []
    for crop_label, our_crop in KAGGLE_CROP_MAP.items():
        cfg = CROPS_CONFIG[our_crop]
        subset = kaggle_df[kaggle_df["label"] == crop_label].copy()
        print(f"  {our_crop}: {len(subset)} real Kaggle rows")

        rain_mult = KAGGLE_RAIN_MULTIPLIERS.get(crop_label, 8.0)

        for _, krow in subset.iterrows():
            # Map Kaggle features to our feature space
            temp = float(krow["temperature"])
            humidity = float(krow["humidity"])
            ph = float(krow["ph"])
            kaggle_rain = float(krow["rainfall"])
            kaggle_n = float(krow["N"])
            kaggle_p = float(krow["P"])

            # Transform to our scale using crop-specific seasonal multiplier
            annual_rainfall = np.clip(kaggle_rain * rain_mult, cfg["rain_tol"][0], cfg["rain_tol"][1])
            nitrogen = np.clip(kaggle_n * 1.5, cfg["n_tol"][0], cfg["n_tol"][1])
            soil_moisture = np.clip(humidity, cfg["moist_tol"][0], cfg["moist_tol"][1])
            soil_ph = np.clip(ph, cfg["ph_tol"][0], cfg["ph_tol"][1])

            p_opt_max = cfg["p_opt"][1]
            fert = min(100, (kaggle_p * 1.8 / max(1, p_opt_max)) * 80)
            irrig = min(100, humidity * 0.9)
            area_ha = float(np.random.choice(AREA_HA_CHOICES))

            row = compute_row(
                our_crop, cfg, temp, soil_moisture, soil_ph,
                annual_rainfall, nitrogen, fert, irrig, area_ha,
                data_source="kaggle_real", is_synthetic=False
            )
            rows.append(row)

    print(f"  Total real Kaggle rows converted: {len(rows)}")
    return rows


def augment_kaggle_rows(real_rows, augment_to=900):
    """Augment real rows with Gaussian noise + explicit stress/extreme samples."""
    augmented = []
    crops_in_real = set(r["crop"] for r in real_rows)
    for crop_name in crops_in_real:
        cfg = CROPS_CONFIG[crop_name]
        crop_real = [r for r in real_rows if r["crop"] == crop_name]
        # Keep all original rows
        augmented.extend(crop_real)

        # Need (augment_to - len(crop_real)) more
        needed = augment_to - len(crop_real)
        if needed <= 0:
            continue

        # Compute distribution stats from real rows
        temps = [r["temperature"] for r in crop_real]
        moists = [r["soil_moisture"] for r in crop_real]
        phs = [r["soil_ph"] for r in crop_real]
        rains = [r["annual_rainfall"] for r in crop_real]
        ns = [r["nitrogen"] for r in crop_real]

        # Split: 60% Gaussian around real, 15% single stress, 15% multi stress, 10% extreme
        n_gauss = int(needed * 0.60)
        n_single = int(needed * 0.15)
        n_multi = int(needed * 0.15)
        n_extreme = needed - n_gauss - n_single - n_multi

        for idx in range(needed):
            area_ha = float(np.random.choice(AREA_HA_CHOICES))

            if idx < n_gauss:
                # Gaussian noise around real rows
                seed = random.choice(crop_real)
                temp = np.clip(seed["temperature"] + np.random.normal(0, np.std(temps) * 0.3),
                               cfg["temp_tol"][0] - 2, cfg["temp_tol"][1] + 2)
                moist = np.clip(seed["soil_moisture"] + np.random.normal(0, np.std(moists) * 0.3),
                                10, 98)
                ph = np.clip(seed["soil_ph"] + np.random.normal(0, np.std(phs) * 0.3),
                             3.5, 9.5)
                rain = np.clip(seed["annual_rainfall"] + np.random.normal(0, np.std(rains) * 0.3),
                               50, cfg["rain_tol"][1])
                n_val = np.clip(seed["nitrogen"] + np.random.normal(0, np.std(ns) * 0.3),
                                5, cfg["n_tol"][1])
                fert = np.clip(seed["fertilizer_level"] + np.random.normal(0, 8), 20, 100)
                irrig = np.clip(seed["irrigation_level"] + np.random.normal(0, 8), 20, 100)

            elif idx < n_gauss + n_single:
                # Single stress: one parameter pushed to extreme
                temp = np.random.uniform(cfg["temp_opt"][0] - 2, cfg["temp_opt"][1] + 2)
                moist = np.random.uniform(cfg["moist_opt"][0] - 5, cfg["moist_opt"][1] + 5)
                ph = np.random.uniform(cfg["ph_opt"][0] - 0.3, cfg["ph_opt"][1] + 0.3)
                rain = np.random.uniform(cfg["rain_opt"][0] - 50, cfg["rain_opt"][1] + 50)
                n_val = np.random.uniform(cfg["n_opt"][0] - 10, cfg["n_opt"][1] + 10)
                stress = random.choice(["temp", "moist", "ph", "rain", "n"])
                if stress == "temp":
                    temp = random.choice([random.uniform(5, cfg["temp_tol"][0]),
                                          random.uniform(cfg["temp_tol"][1], 44)])
                elif stress == "moist":
                    moist = random.choice([random.uniform(10, cfg["moist_tol"][0]),
                                           random.uniform(cfg["moist_tol"][1], 98)])
                elif stress == "ph":
                    ph = random.choice([random.uniform(4.0, cfg["ph_tol"][0]),
                                        random.uniform(cfg["ph_tol"][1], 9.0)])
                elif stress == "rain":
                    rain = random.choice([random.uniform(50, cfg["rain_tol"][0]),
                                          random.uniform(cfg["rain_tol"][1], 3200)])
                else:
                    n_val = random.uniform(5, cfg["n_tol"][0])
                fert = round(random.uniform(30, 100), 1)
                irrig = round(random.uniform(20, 100), 1)

            elif idx < n_gauss + n_single + n_multi:
                # Multi stress: multiple parameters out of range
                temp = random.choice([random.uniform(6, cfg["temp_tol"][0]),
                                      random.uniform(cfg["temp_tol"][1] - 1, 43)])
                moist = random.choice([random.uniform(12, cfg["moist_tol"][0]),
                                       random.uniform(cfg["moist_tol"][1] - 2, 98)])
                ph = random.choice([random.uniform(4.0, cfg["ph_tol"][0] + 0.2),
                                    random.uniform(cfg["ph_tol"][1] - 0.2, 8.9)])
                rain = random.choice([random.uniform(80, cfg["rain_tol"][0]),
                                      random.uniform(cfg["rain_tol"][1], 3000)])
                n_val = random.uniform(5, cfg["n_tol"][0] + 10)
                fert = round(random.uniform(30, 100), 1)
                irrig = round(random.uniform(20, 100), 1)

            else:
                # Extreme: all parameters terrible
                temp = random.uniform(37, 44) if cfg["temp_opt"][1] < 35 else random.uniform(5, 14)
                moist = random.uniform(10, 20)
                ph = random.uniform(4.0, 4.8)
                rain = random.uniform(50, 200)
                n_val = random.uniform(5, 20)
                fert = round(random.uniform(20, 50), 1)
                irrig = round(random.uniform(15, 40), 1)

            row = compute_row(
                crop_name, cfg, float(temp), float(moist), float(ph),
                float(rain), float(n_val), float(fert), float(irrig), area_ha,
                data_source="kaggle_augmented", is_synthetic=True
            )
            augmented.append(row)

        real_ct = len(crop_real)
        aug_ct = needed
        print(f"  {crop_name}: {real_ct} real + {aug_ct} augmented = {real_ct + aug_ct} total")

    return augmented


def generate_icar_fao_rows(num_per_crop=900):
    """Generate ICAR/FAO calibrated rows for crops NOT in Kaggle dataset."""
    non_kaggle_crops = [c for c in CROPS_CONFIG if c not in KAGGLE_CROP_MAP.values()]
    rows = []

    for crop_name in non_kaggle_crops:
        cfg = CROPS_CONFIG[crop_name]
        for _ in range(num_per_crop):
            mode = np.random.choice(
                ["optimal", "moderate", "single_stress", "multi_stress", "extreme", "uniform"],
                p=[0.25, 0.25, 0.15, 0.15, 0.10, 0.10]
            )

            if mode == "optimal":
                temp = np.random.uniform(cfg["temp_opt"][0], cfg["temp_opt"][1])
                moist = np.random.uniform(cfg["moist_opt"][0], cfg["moist_opt"][1])
                ph = np.random.uniform(cfg["ph_opt"][0], cfg["ph_opt"][1])
                rain = np.random.uniform(cfg["rain_opt"][0], cfg["rain_opt"][1])
                n = np.random.uniform(cfg["n_opt"][0], cfg["n_opt"][1])
            elif mode == "moderate":
                temp = np.random.uniform(cfg["temp_tol"][0] + 3, cfg["temp_tol"][1] - 3)
                moist = np.random.uniform(cfg["moist_tol"][0] + 6, cfg["moist_tol"][1] - 6)
                ph = np.random.uniform(cfg["ph_tol"][0] + 0.4, cfg["ph_tol"][1] - 0.4)
                rain = np.random.uniform(cfg["rain_tol"][0] + 100, cfg["rain_tol"][1] - 100)
                n = np.random.uniform(cfg["n_tol"][0] + 10, cfg["n_tol"][1] - 10)
            elif mode == "single_stress":
                temp = np.random.uniform(cfg["temp_opt"][0] - 2, cfg["temp_opt"][1] + 2)
                moist = np.random.uniform(cfg["moist_opt"][0] - 5, cfg["moist_opt"][1] + 5)
                ph = np.random.uniform(cfg["ph_opt"][0] - 0.3, cfg["ph_opt"][1] + 0.3)
                rain = np.random.uniform(cfg["rain_opt"][0] - 50, cfg["rain_opt"][1] + 50)
                n = np.random.uniform(cfg["n_opt"][0] - 10, cfg["n_opt"][1] + 10)
                stress = random.choice(["temp", "moist", "ph", "rain", "n"])
                if stress == "temp":
                    temp = random.choice([random.uniform(5, cfg["temp_tol"][0]),
                                          random.uniform(cfg["temp_tol"][1], 44)])
                elif stress == "moist":
                    moist = random.choice([random.uniform(10, cfg["moist_tol"][0]),
                                           random.uniform(cfg["moist_tol"][1], 98)])
                elif stress == "ph":
                    ph = random.choice([random.uniform(4.0, cfg["ph_tol"][0]),
                                        random.uniform(cfg["ph_tol"][1], 9.0)])
                elif stress == "rain":
                    rain = random.choice([random.uniform(50, cfg["rain_tol"][0]),
                                          random.uniform(cfg["rain_tol"][1], 3200)])
                elif stress == "n":
                    n = random.uniform(5, cfg["n_tol"][0])
            elif mode == "multi_stress":
                temp = random.choice([random.uniform(6, cfg["temp_tol"][0]),
                                      random.uniform(cfg["temp_tol"][1] - 1, 43)])
                moist = random.choice([random.uniform(12, cfg["moist_tol"][0]),
                                       random.uniform(cfg["moist_tol"][1] - 2, 98)])
                ph = random.choice([random.uniform(4.0, cfg["ph_tol"][0] + 0.2),
                                    random.uniform(cfg["ph_tol"][1] - 0.2, 8.9)])
                rain = random.choice([random.uniform(80, cfg["rain_tol"][0]),
                                      random.uniform(cfg["rain_tol"][1], 3000)])
                n = random.uniform(5, cfg["n_tol"][0] + 10)
            elif mode == "extreme":
                temp = random.uniform(37, 44) if cfg["temp_opt"][1] < 35 else random.uniform(5, 14)
                moist = random.uniform(10, 20)
                ph = random.uniform(4.0, 4.8)
                rain = random.uniform(50, 200)
                n = random.uniform(5, 20)
            else:  # uniform
                temp = random.uniform(5, 45)
                moist = random.uniform(10, 100)
                ph = random.uniform(4.0, 9.0)
                rain = random.uniform(100, 3000)
                n = random.uniform(0, 200)

            fert = round(random.uniform(30, 100), 1)
            irrig = round(random.uniform(20, 100), 1)
            area_ha = float(np.random.choice(AREA_HA_CHOICES))

            row = compute_row(
                crop_name, cfg, float(temp), float(moist), float(ph),
                float(rain), float(n), float(fert), float(irrig), area_ha,
                data_source="icar_fao_calibrated", is_synthetic=True
            )
            rows.append(row)

        print(f"  {crop_name}: {num_per_crop} ICAR/FAO calibrated rows generated")

    return rows


def train_and_save():
    """Main training pipeline."""
    random.seed(42)
    np.random.seed(42)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("  FARM WISE AI - RETRAIN WITH KAGGLE REAL DATA")
    print("=" * 65)

    # Step 1: Load real Kaggle rows for 4 crops
    print("\n[STEP 1] Loading Kaggle Crop Recommendation real data...")
    real_rows = load_kaggle_rows()

    # Step 2: Augment real rows to 900 per crop
    print("\n[STEP 2] Augmenting Kaggle rows with Gaussian noise...")
    augmented_rows = augment_kaggle_rows(real_rows, augment_to=900)

    # Step 3: Generate ICAR/FAO rows for 5 non-Kaggle crops
    print("\n[STEP 3] Generating ICAR/FAO calibrated data for non-Kaggle crops...")
    icar_rows = generate_icar_fao_rows(num_per_crop=900)

    # Step 4: Combine all
    all_rows = augmented_rows + icar_rows
    df = pd.DataFrame(all_rows)
    df.to_csv(DATASET_PATH, index=False)
    print(f"\n[STEP 4] Combined dataset: {len(df)} rows saved to {DATASET_PATH}")
    print(f"  Data source breakdown:")
    print(df["data_source"].value_counts().to_string())
    print(f"  Crop counts:")
    print(df["crop"].value_counts().to_string())

    # Step 5: Train per-crop models
    print("\n[STEP 5] Training per-crop Random Forest models...")
    num_features = ["area_ha", "temperature", "soil_moisture", "soil_ph",
                    "annual_rainfall", "nitrogen", "fertilizer_level", "irrigation_level"]
    reg_target_cols = ["yield_t_ha", "water_mm", "harvest_days",
                       "co2_credits", "input_cost", "success_rate"]

    crops = sorted(list(CROPS_CONFIG.keys()))
    crop_models = {}
    metrics_summary = {}

    for crop_name in crops:
        c_df = df[df["crop"] == crop_name]
        X = c_df[num_features]
        Y_reg = c_df[reg_target_cols]
        y_clf = c_df["condition"]

        X_tr, X_te, Y_tr, Y_te, yc_tr, yc_te = train_test_split(
            X, Y_reg, y_clf, test_size=0.20, random_state=42, stratify=y_clf
        )

        reg = MultiOutputRegressor(
            RandomForestRegressor(
                n_estimators=100, max_depth=16, min_samples_split=3,
                random_state=42, n_jobs=-1
            )
        )
        reg.fit(X_tr, Y_tr)

        clf = RandomForestClassifier(
            n_estimators=100, max_depth=16, min_samples_split=3,
            random_state=42, n_jobs=-1
        )
        clf.fit(X_tr, yc_tr)

        Y_pred = reg.predict(X_te)
        yc_pred = clf.predict(X_te)

        crop_metrics = {
            "regression": {},
            "condition_accuracy": round(float(accuracy_score(yc_te, yc_pred)), 4)
        }
        for i, col in enumerate(reg_target_cols):
            crop_metrics["regression"][col] = {
                "MAE": round(float(mean_absolute_error(Y_te[col], Y_pred[:, i])), 3),
                "R2": round(float(r2_score(Y_te[col], Y_pred[:, i])), 4)
            }

        metrics_summary[crop_name] = crop_metrics
        crop_models[crop_name] = {
            "regressor": reg,
            "classifier": clf
        }

        yield_r2 = crop_metrics["regression"]["yield_t_ha"]["R2"]
        cond_acc = crop_metrics["condition_accuracy"] * 100
        data_src = "KAGGLE+AUG" if crop_name in KAGGLE_CROP_MAP.values() else "ICAR/FAO"
        print(f"  [OK] {crop_name:12s} | Yield R2: {yield_r2:6.3f} | Cond Acc: {cond_acc:5.1f}% | Source: {data_src}")

    # Step 6: Train global fallback model
    print("\n[STEP 6] Training global fallback model...")
    crop_dummies = pd.get_dummies(df["crop"], prefix="crop", dtype=float)
    X_global = pd.concat([df[num_features], crop_dummies], axis=1)
    global_features = list(X_global.columns)

    X_gtr, X_gte, Y_gtr, Y_gte, ycg_tr, ycg_te = train_test_split(
        X_global, df[reg_target_cols], df["condition"],
        test_size=0.20, random_state=42
    )
    global_reg = MultiOutputRegressor(
        RandomForestRegressor(
            n_estimators=100, max_depth=16, random_state=42, n_jobs=-1
        )
    )
    global_reg.fit(X_gtr, Y_gtr)
    global_clf = RandomForestClassifier(
        n_estimators=100, max_depth=16, random_state=42, n_jobs=-1
    )
    global_clf.fit(X_gtr, ycg_tr)

    global_yield_r2 = round(float(r2_score(Y_gte["yield_t_ha"], global_reg.predict(X_gte)[:, 0])), 4)
    global_cond_acc = round(float(accuracy_score(ycg_te, global_clf.predict(X_gte))), 4)
    print(f"  Global Yield R2: {global_yield_r2} | Global Cond Acc: {global_cond_acc * 100:.1f}%")

    # Step 7: Save model bundle (compatible with simulation_model.py)
    print("\n[STEP 7] Saving model bundle...")
    model_bundle = {
        "crop_models": crop_models,
        "global_reg": global_reg,
        "global_clf": global_clf,
        "global_features": global_features,
        "num_features": num_features,
        "reg_target_cols": reg_target_cols,
        "crops": crops,
        "crops_config": CROPS_CONFIG
    }
    joblib.dump(model_bundle, MODEL_BUNDLE_PATH, compress=3)
    print(f"  Model bundle saved to {MODEL_BUNDLE_PATH}")

    # Step 8: Save schema
    kaggle_crops = list(KAGGLE_CROP_MAP.values())
    icar_crops = [c for c in crops if c not in kaggle_crops]
    schema = {
        "model_name": "Farm Wise AI Crop Simulator (Kaggle + ICAR/FAO Retrained)",
        "data_sources": {
            "kaggle_real": f"Kaggle Crop Recommendation Dataset - {len(kaggle_crops)} crops with 100 real sensor rows each",
            "kaggle_augmented": "Gaussian noise augmentation around real Kaggle distributions",
            "icar_fao_calibrated": f"ICAR/FAO calibrated synthetic generation for {len(icar_crops)} crops"
        },
        "kaggle_crops": kaggle_crops,
        "icar_fao_crops": icar_crops,
        "features": num_features,
        "crops": crops,
        "regression_targets": reg_target_cols,
        "classification_target": "condition",
        "condition_classes": ["Good", "Moderate", "Poor"],
        "configurable_prices_per_tonne": {c: CROPS_CONFIG[c]["price_per_tonne"] for c in crops},
        "total_dataset_rows": len(df),
        "real_data_rows": len([r for r in all_rows if not r["is_synthetic"]])
    }
    with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"  Schema saved to {SCHEMA_PATH}")

    # Step 9: Save metrics
    metrics = {
        "model_version": "Kaggle + ICAR/FAO Retrained",
        "total_dataset_rows": len(df),
        "real_data_rows": schema["real_data_rows"],
        "note": "Retrained using Kaggle Crop Recommendation real sensor data for Rice/Maize/Cotton/Banana, "
                "with ICAR/FAO calibrated generation for Wheat/Tomato/Sugarcane/Soybean/Groundnut.",
        "crop_metrics": metrics_summary,
        "global_yield_r2": global_yield_r2,
        "global_condition_accuracy": global_cond_acc
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"  Metrics saved to {METRICS_PATH}")

    # Final Summary
    print("\n" + "=" * 65)
    print("  RETRAINING COMPLETE - SUMMARY")
    print("=" * 65)
    print(f"  Total dataset rows: {len(df)}")
    print(f"  Real Kaggle rows:   {schema['real_data_rows']}")
    print(f"  Kaggle crops:       {', '.join(kaggle_crops)}")
    print(f"  ICAR/FAO crops:     {', '.join(icar_crops)}")
    print(f"  Global Yield R2:    {global_yield_r2}")
    print(f"  Global Cond Acc:    {global_cond_acc * 100:.1f}%")
    print("=" * 65)


if __name__ == "__main__":
    train_and_save()
