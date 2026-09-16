import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
import random

CROP_DATA = {
    "Rice": {"n_range": (80, 120), "p_range": (40, 60), "k_range": (40, 60), "ph_range": (6.0, 7.0), "temp_range": (22, 35), "humidity_range": (80, 95), "rainfall_range": (150, 300), "seasons": ["Kharif"], "soil_types": ["Clayey", "Loamy"], "expected_yield_range": (25, 60), "price_per_quintal": 2183, "fertilizer": "Urea + DAP + Potash (120:60:60 kg/ha)", "water_req": "1200-2000 mm", "harvest_time": "120-150 days", "alternatives": ["Maize", "Sugarcane"]},
    "Wheat": {"n_range": (100, 150), "p_range": (50, 80), "k_range": (40, 60), "ph_range": (6.0, 7.5), "temp_range": (10, 25), "humidity_range": (50, 70), "rainfall_range": (50, 100), "seasons": ["Rabi"], "soil_types": ["Loamy", "Clay Loam"], "expected_yield_range": (30, 55), "price_per_quintal": 2275, "fertilizer": "Urea + SSP (120:60 kg/ha)", "water_req": "450-650 mm", "harvest_time": "100-140 days", "alternatives": ["Barley", "Mustard"]},
    "Maize": {"n_range": (100, 140), "p_range": (60, 80), "k_range": (40, 60), "ph_range": (5.8, 7.0), "temp_range": (21, 32), "humidity_range": (60, 80), "rainfall_range": (60, 110), "seasons": ["Kharif", "Rabi"], "soil_types": ["Sandy Loam", "Loamy"], "expected_yield_range": (30, 70), "price_per_quintal": 2090, "fertilizer": "NPK 120:60:40 kg/ha", "water_req": "500-800 mm", "harvest_time": "90-120 days", "alternatives": ["Sorghum", "Millet"]},
    "Tomato": {"n_range": (100, 150), "p_range": (80, 120), "k_range": (80, 120), "ph_range": (6.0, 7.0), "temp_range": (20, 30), "humidity_range": (60, 75), "rainfall_range": (40, 80), "seasons": ["Kharif", "Rabi", "Zaid"], "soil_types": ["Sandy Loam", "Loamy", "Red"], "expected_yield_range": (200, 500), "price_per_quintal": 2450, "fertilizer": "NPK 100:80:80 + Micronutrients", "water_req": "400-600 mm", "harvest_time": "70-90 days", "alternatives": ["Brinjal", "Chilli"]},
    "Cotton": {"n_range": (100, 160), "p_range": (40, 80), "k_range": (40, 80), "ph_range": (7.0, 8.0), "temp_range": (25, 38), "humidity_range": (60, 80), "rainfall_range": (50, 100), "seasons": ["Kharif"], "soil_types": ["Black", "Clayey"], "expected_yield_range": (15, 35), "price_per_quintal": 6620, "fertilizer": "NPK 150:60:60 + Boron", "water_req": "700-1200 mm", "harvest_time": "160-200 days", "alternatives": ["Soybean", "Groundnut"]},
    "Sugarcane": {"n_range": (200, 300), "p_range": (80, 120), "k_range": (100, 150), "ph_range": (6.5, 7.5), "temp_range": (27, 38), "humidity_range": (70, 85), "rainfall_range": (150, 250), "seasons": ["Kharif", "Annual"], "soil_types": ["Loamy", "Black"], "expected_yield_range": (600, 1000), "price_per_quintal": 340, "fertilizer": "NPK 200:80:80 + Organic FYM", "water_req": "1500-2500 mm", "harvest_time": "300-360 days", "alternatives": ["Banana", "Rice"]},
    "Soybean": {"n_range": (20, 50), "p_range": (60, 90), "k_range": (40, 70), "ph_range": (6.0, 7.0), "temp_range": (20, 30), "humidity_range": (60, 75), "rainfall_range": (60, 100), "seasons": ["Kharif"], "soil_types": ["Black", "Loamy"], "expected_yield_range": (18, 35), "price_per_quintal": 4600, "fertilizer": "Rhizobium + NPK 20:60:40", "water_req": "450-700 mm", "harvest_time": "90-120 days", "alternatives": ["Pigeonpea", "Cotton"]},
    "Groundnut": {"n_range": (20, 40), "p_range": (50, 80), "k_range": (60, 90), "ph_range": (6.0, 7.0), "temp_range": (25, 35), "humidity_range": (50, 70), "rainfall_range": (50, 100), "seasons": ["Kharif", "Rabi"], "soil_types": ["Sandy Loam", "Red"], "expected_yield_range": (15, 30), "price_per_quintal": 5850, "fertilizer": "NPK 25:50:40 + Gypsum", "water_req": "500-700 mm", "harvest_time": "110-130 days", "alternatives": ["Soybean", "Sesame"]},
}

class CropRecommendationModel:
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.crops = list(CROP_DATA.keys())
        self.soil_types = ["Sandy Loam", "Loamy", "Clay Loam", "Clayey", "Black", "Red"]
        self.seasons = ["Kharif", "Rabi", "Zaid", "Annual"]
        self._train()

    def _generate_data(self, n_samples=4000):
        records, labels = [], []
        for _ in range(n_samples):
            crop = random.choice(self.crops)
            info = CROP_DATA[crop]
            records.append([
                max(0, random.uniform(*info["n_range"]) + random.gauss(0, 4)),
                max(0, random.uniform(*info["p_range"]) + random.gauss(0, 3)),
                max(0, random.uniform(*info["k_range"]) + random.gauss(0, 3)),
                max(4.0, min(9.0, random.uniform(*info["ph_range"]))),
                random.uniform(*info["temp_range"]),
                random.uniform(*info["humidity_range"]),
                random.uniform(*info["rainfall_range"]),
                self.soil_types.index(random.choice(info["soil_types"])) if random.choice(info["soil_types"]) in self.soil_types else 0,
                self.seasons.index(random.choice(info["seasons"])) if random.choice(info["seasons"]) in self.seasons else 0,
            ])
            labels.append(crop)
        return np.array(records), np.array(labels)

    def _train(self):
        X, y = self._generate_data()
        X_scaled = self.scaler.fit_transform(X)
        self.label_encoder.fit(self.crops)
        y_encoded = self.label_encoder.transform(y)
        self.model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42)
        self.model.fit(X_scaled, y_encoded)

    def predict(self, n, p, k, ph, temp, humidity, rainfall, soil_type, season, land_area=1.0):
        soil_enc = self.soil_types.index(soil_type) if soil_type in self.soil_types else 0
        season_enc = self.seasons.index(season) if season in self.seasons else 0

        features = self.scaler.transform([[n, p, k, ph, temp, humidity, rainfall, soil_enc, season_enc]])
        probas = self.model.predict_proba(features)[0]
        top_indices = np.argsort(probas)[::-1]

        best_crop = self.label_encoder.inverse_transform([top_indices[0]])[0]
        confidence = min(99.0, max(65.0, float(probas[top_indices[0]] * 100)))

        info = CROP_DATA.get(best_crop, {})
        ymin, ymax = info.get("expected_yield_range", (20, 50))
        expected_yield = round(random.uniform(ymin, ymax) * land_area, 1)
        price = info.get("price_per_quintal", 2200)
        expected_profit = int(expected_yield * price * 0.72)

        alts = [self.label_encoder.inverse_transform([i])[0] for i in top_indices[1:4]]

        return {
            "recommended_crop": best_crop,
            "confidence": round(confidence, 1),
            "expected_yield": expected_yield,
            "expected_profit": expected_profit,
            "fertilizer": info.get("fertilizer", "NPK 100:60:40 kg/ha"),
            "water_requirement": info.get("water_req", "500-800 mm"),
            "harvest_time": info.get("harvest_time", "90-120 days"),
            "alternative_crops": alts,
        }

_crop_model_instance = None
def get_crop_model():
    global _crop_model_instance
    if _crop_model_instance is None:
        _crop_model_instance = CropRecommendationModel()
    return _crop_model_instance
