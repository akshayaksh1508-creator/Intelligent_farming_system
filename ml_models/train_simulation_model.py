# ============================================================
# Farm Wise AI – Stage 1 Crop Simulator ML Training Pipeline
# Synthetic/Prototype Dataset Generator and Model Trainer
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
DATASET_PATH = DATA_DIR / "simulation_results_prototype_dataset.csv"
MODEL_BUNDLE_PATH = BASE_DIR / "simulation_results_models.joblib"
SCHEMA_PATH = BASE_DIR / "simulation_results_schema.json"
METRICS_PATH = BASE_DIR / "simulation_results_metrics.json"

CROPS_CONFIG = {
    "Rice": {
        "temp_opt": (22, 32), "temp_tol": (15, 42),
        "moist_opt": (65, 85), "moist_tol": (40, 95),
        "ph_opt": (5.5, 7.0), "ph_tol": (4.5, 8.5),
        "rain_opt": (1100, 1800), "rain_tol": (500, 3000),
        "n_opt": (80, 130), "n_tol": (30, 200),
        "base_yield": 4.5, "base_water_mm": 1200, "base_days": 120,
        "base_cost_ha": 4800, "price_per_tonne": 22000, "co2_factor": 1.2
    },
    "Wheat": {
        "temp_opt": (14, 24), "temp_tol": (8, 35),
        "moist_opt": (45, 65), "moist_tol": (25, 85),
        "ph_opt": (6.0, 7.5), "ph_tol": (5.0, 8.8),
        "rain_opt": (400, 750), "rain_tol": (150, 1500),
        "n_opt": (90, 140), "n_tol": (30, 200),
        "base_yield": 4.0, "base_water_mm": 500, "base_days": 110,
        "base_cost_ha": 4500, "price_per_tonne": 22750, "co2_factor": 1.0
    },
    "Maize": {
        "temp_opt": (18, 30), "temp_tol": (10, 40),
        "moist_opt": (45, 65), "moist_tol": (20, 85),
        "ph_opt": (5.8, 7.2), "ph_tol": (4.8, 8.5),
        "rain_opt": (550, 850), "rain_tol": (200, 1800),
        "n_opt": (70, 130), "n_tol": (25, 200),
        "base_yield": 5.1, "base_water_mm": 550, "base_days": 95,
        "base_cost_ha": 4600, "price_per_tonne": 3035, "co2_factor": 1.1
    },
    "Tomato": {
        "temp_opt": (18, 28), "temp_tol": (10, 38),
        "moist_opt": (50, 70), "moist_tol": (25, 90),
        "ph_opt": (6.0, 7.0), "ph_tol": (5.0, 8.2),
        "rain_opt": (450, 750), "rain_tol": (150, 1600),
        "n_opt": (80, 140), "n_tol": (25, 200),
        "base_yield": 26.0, "base_water_mm": 600, "base_days": 80,
        "base_cost_ha": 12000, "price_per_tonne": 2500, "co2_factor": 0.8
    },
    "Cotton": {
        "temp_opt": (24, 36), "temp_tol": (16, 44),
        "moist_opt": (40, 60), "moist_tol": (20, 80),
        "ph_opt": (6.2, 8.0), "ph_tol": (5.2, 8.8),
        "rain_opt": (550, 900), "rain_tol": (250, 1800),
        "n_opt": (90, 150), "n_tol": (30, 200),
        "base_yield": 2.3, "base_water_mm": 750, "base_days": 175,
        "base_cost_ha": 7500, "price_per_tonne": 66200, "co2_factor": 0.9
    },
    "Sugarcane": {
        "temp_opt": (22, 36), "temp_tol": (15, 45),
        "moist_opt": (65, 85), "moist_tol": (35, 95),
        "ph_opt": (6.0, 7.6), "ph_tol": (5.0, 8.6),
        "rain_opt": (1300, 2200), "rain_tol": (600, 3200),
        "n_opt": (140, 220), "n_tol": (50, 250),
        "base_yield": 75.0, "base_water_mm": 1800, "base_days": 330,
        "base_cost_ha": 15000, "price_per_tonne": 3500, "co2_factor": 2.5
    },
    "Soybean": {
        "temp_opt": (20, 32), "temp_tol": (12, 40),
        "moist_opt": (50, 70), "moist_tol": (25, 85),
        "ph_opt": (6.0, 7.2), "ph_tol": (5.0, 8.5),
        "rain_opt": (500, 850), "rain_tol": (200, 1600),
        "n_opt": (30, 70), "n_tol": (10, 160),
        "base_yield": 2.8, "base_water_mm": 500, "base_days": 100,
        "base_cost_ha": 4200, "price_per_tonne": 46000, "co2_factor": 1.4
    },
    "Groundnut": {
        "temp_opt": (22, 34), "temp_tol": (14, 42),
        "moist_opt": (45, 65), "moist_tol": (20, 85),
        "ph_opt": (5.8, 7.2), "ph_tol": (4.8, 8.5),
        "rain_opt": (450, 750), "rain_tol": (200, 1500),
        "n_opt": (25, 60), "n_tol": (10, 150),
        "base_yield": 2.5, "base_water_mm": 480, "base_days": 115,
        "base_cost_ha": 4800, "price_per_tonne": 58500, "co2_factor": 1.0
    },
    "Banana": {
        "temp_opt": (22, 36), "temp_tol": (14, 44),
        "moist_opt": (60, 80), "moist_tol": (35, 95),
        "ph_opt": (5.8, 7.2), "ph_tol": (4.8, 8.4),
        "rain_opt": (1100, 1900), "rain_tol": (500, 3000),
        "n_opt": (120, 190), "n_tol": (40, 240),
        "base_yield": 36.0, "base_water_mm": 1400, "base_days": 270,
        "base_cost_ha": 14000, "price_per_tonne": 2500, "co2_factor": 1.8
    }
}

def calc_fit(val, opt_range, tol_range):
    omin, omax = opt_range
    tmin, tmax = tol_range
    if omin <= val <= omax:
        return 1.0
    elif val < omin:
        if val <= tmin: return 0.05
        return 0.05 + 0.95 * (val - tmin) / (omin - tmin)
    else:
        if val >= tmax: return 0.05
        return 0.05 + 0.95 * (tmax - val) / (tmax - omax)

def generate_synthetic_dataset(num_samples_per_crop=900, seed=42):
    random.seed(seed)
    np.random.seed(seed)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    for crop_name, cfg in CROPS_CONFIG.items():
        for _ in range(num_samples_per_crop):
            area_ha = round(float(np.random.choice([0.25, 0.5, 1.0, 1.5, 2.0, 2.25, 3.0, 3.5, 4.0, 5.0, 6.25, 7.5, 9.0, 10.0, 12.25, 16.0])), 2)
            mode = np.random.choice(["optimal", "moderate", "single_stress", "multi_stress", "extreme", "uniform"], p=[0.25, 0.25, 0.15, 0.15, 0.10, 0.10])
            
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
                stress_factor = random.choice(["temp", "moist", "ph", "rain", "n"])
                if stress_factor == "temp": temp = random.choice([random.uniform(5, cfg["temp_tol"][0]), random.uniform(cfg["temp_tol"][1], 44)])
                elif stress_factor == "moist": moist = random.choice([random.uniform(10, cfg["moist_tol"][0]), random.uniform(cfg["moist_tol"][1], 98)])
                elif stress_factor == "ph": ph = random.choice([random.uniform(4.0, cfg["ph_tol"][0]), random.uniform(cfg["ph_tol"][1], 9.0)])
                elif stress_factor == "rain": rain = random.choice([random.uniform(50, cfg["rain_tol"][0]), random.uniform(cfg["rain_tol"][1], 3200)])
                elif stress_factor == "n": n = random.uniform(5, cfg["n_tol"][0])
            elif mode == "multi_stress":
                temp = random.choice([random.uniform(6, cfg["temp_tol"][0]), random.uniform(cfg["temp_tol"][1] - 1, 43)])
                moist = random.choice([random.uniform(12, cfg["moist_tol"][0]), random.uniform(cfg["moist_tol"][1] - 2, 98)])
                ph = random.choice([random.uniform(4.0, cfg["ph_tol"][0] + 0.2), random.uniform(cfg["ph_tol"][1] - 0.2, 8.9)])
                rain = random.choice([random.uniform(80, cfg["rain_tol"][0]), random.uniform(cfg["rain_tol"][1], 3000)])
                n = random.uniform(5, cfg["n_tol"][0] + 10)
            elif mode == "extreme":
                temp = random.uniform(37, 44) if cfg["temp_opt"][1] < 35 else random.uniform(5, 14)
                moist = random.uniform(10, 20)
                ph = random.uniform(4.0, 4.8)
                rain = random.uniform(50, 200)
                n = random.uniform(5, 20)
            else:
                temp = random.uniform(5, 45)
                moist = random.uniform(10, 100)
                ph = random.uniform(4.0, 9.0)
                rain = random.uniform(100, 3000)
                n = random.uniform(0, 200)

            fertilizer_level = round(random.uniform(30, 100), 1)
            irrigation_level = round(random.uniform(20, 100), 1)

            t_fit = calc_fit(temp, cfg["temp_opt"], cfg["temp_tol"])
            p_fit = calc_fit(ph, cfg["ph_opt"], cfg["ph_tol"])
            m_fit = calc_fit(moist, cfg["moist_opt"], cfg["moist_tol"])
            r_fit = calc_fit(rain, cfg["rain_opt"], cfg["rain_tol"])
            n_fit = calc_fit(n, cfg["n_opt"], cfg["n_tol"])

            fits = [t_fit, p_fit, m_fit, r_fit, n_fit]
            S = 0.50 * min(fits) + 0.50 * (sum(fits) / len(fits))
            S = max(0.05, min(1.0, S))

            noise_yield = np.random.normal(1.0, 0.02)
            yield_t_ha = round(max(0.15, cfg["base_yield"] * (0.15 + 0.85 * S) * noise_yield), 2)
            success_rate = int(round(max(5, min(99, S * 100 + np.random.normal(0, 1.5)))))
            
            water_stress_penalty = 1.0 + 0.30 * (1.0 - m_fit)
            water_mm = int(round(cfg["base_water_mm"] * water_stress_penalty * np.random.normal(1.0, 0.02)))

            days_modifier = 1.0 + 0.12 * (1.0 - t_fit)
            harvest_days = int(round(cfg["base_days"] * days_modifier * np.random.normal(1.0, 0.015)))

            co2_credits = round(max(0.1, cfg["co2_factor"] * area_ha * (0.30 + 0.70 * S) * np.random.normal(1.0, 0.02)), 2)
            
            cost_per_ha = cfg["base_cost_ha"] * (0.85 + 0.20 * (fertilizer_level / 100.0) + 0.10 * (irrigation_level / 100.0))
            input_cost = int(round(cost_per_ha * area_ha * np.random.normal(1.0, 0.02)))
            input_cost = max(500, input_cost)

            season_income = int(round(yield_t_ha * area_ha * cfg["price_per_tonne"]))
            net_roi = round(((season_income - input_cost) / input_cost) * 100.0, 1)

            if S >= 0.75: condition = "Good"
            elif S >= 0.45: condition = "Moderate"
            else: condition = "Poor"

            rows.append({
                "crop": crop_name,
                "area_ha": round(area_ha, 2),
                "temperature": round(temp, 1),
                "soil_moisture": round(moist, 1),
                "soil_ph": round(ph, 2),
                "annual_rainfall": round(rain, 0),
                "nitrogen": round(n, 1),
                "fertilizer_level": fertilizer_level,
                "irrigation_level": irrigation_level,
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
                "is_synthetic": True
            })

    df = pd.DataFrame(rows)
    df.to_csv(DATASET_PATH, index=False)
    print(f"Synthetic dataset created at {DATASET_PATH} with {len(df)} records.")
    return df

def train_and_save_models():
    df = generate_synthetic_dataset(num_samples_per_crop=900)

    num_features = ["area_ha", "temperature", "soil_moisture", "soil_ph", "annual_rainfall", "nitrogen", "fertilizer_level", "irrigation_level"]
    reg_target_cols = ["yield_t_ha", "water_mm", "harvest_days", "co2_credits", "input_cost", "success_rate"]

    crops = sorted(list(CROPS_CONFIG.keys()))
    crop_models = {}
    metrics_summary = {}

    print(f"Training specialized crop models for {len(crops)} crops...")

    for crop_name in crops:
        c_df = df[df["crop"] == crop_name]
        X = c_df[num_features]
        Y_reg = c_df[reg_target_cols]
        y_clf = c_df["condition"]

        X_tr, X_te, Y_tr, Y_te, yc_tr, yc_te = train_test_split(
            X, Y_reg, y_clf, test_size=0.20, random_state=42, stratify=y_clf
        )

        reg = RandomForestRegressor(n_estimators=100, max_depth=16, min_samples_split=3, random_state=42, n_jobs=-1)
        reg.fit(X_tr, Y_tr)
        
        clf = RandomForestClassifier(n_estimators=80, max_depth=12, min_samples_split=3, random_state=42, n_jobs=-1)
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
        print(f"  [OK] {crop_name:10s} | Yield R2: {crop_metrics['regression']['yield_t_ha']['R2']:6.3f} | Cost R2: {crop_metrics['regression']['input_cost']['R2']:6.3f} | Cond Acc: {crop_metrics['condition_accuracy']*100:.1f}%")

    # Unified global model as fallback
    crop_dummies = pd.get_dummies(df["crop"], prefix="crop", dtype=float)
    X_global = pd.concat([df[num_features], crop_dummies], axis=1)
    global_features = list(X_global.columns)

    X_gtr, X_gte, Y_gtr, Y_gte, ycg_tr, ycg_te = train_test_split(
        X_global, df[reg_target_cols], df["condition"], test_size=0.20, random_state=42
    )
    global_reg = RandomForestRegressor(n_estimators=120, max_depth=18, random_state=42, n_jobs=-1)
    global_reg.fit(X_gtr, Y_gtr)
    global_clf = RandomForestClassifier(n_estimators=80, max_depth=14, random_state=42, n_jobs=-1)
    global_clf.fit(X_gtr, ycg_tr)

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
    print(f"Model bundle saved to {MODEL_BUNDLE_PATH}")

    schema = {
        "model_name": "Farm Wise AI Crop Simulator (Stage 1 Prototype)",
        "data_source": "SYNTHETIC/PROTOTYPE DATA",
        "hardware_compatibility": "Compatible with future ESP32 sensor inputs (pH, moisture, NPK, temp, rain)",
        "features": num_features,
        "crops": crops,
        "regression_targets": reg_target_cols,
        "classification_target": "condition",
        "condition_classes": ["Good", "Moderate", "Poor"],
        "configurable_prices_per_tonne": {c: CROPS_CONFIG[c]["price_per_tonne"] for c in crops}
    }
    with open(SCHEMA_PATH, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"Schema saved to {SCHEMA_PATH}")

    metrics = {
        "model_version": "Stage 1 Prototype",
        "total_dataset_rows": len(df),
        "note": "Prototype model trained using synthetic data. Real-world accuracy requires real farm/hardware data.",
        "crop_metrics": metrics_summary,
        "global_yield_r2": round(float(r2_score(Y_gte["yield_t_ha"], global_reg.predict(X_gte)[:, 0])), 4),
        "global_condition_accuracy": round(float(accuracy_score(ycg_te, global_clf.predict(X_gte))), 4)
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to {METRICS_PATH}")

if __name__ == "__main__":
    train_and_save_models()
