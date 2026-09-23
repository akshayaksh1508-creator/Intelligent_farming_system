import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from ml_models.simulation_model import predict_simulation

def run_tests():
    print("=" * 65)
    print("       FARM WISE AI - SIMULATION ML MODEL TEST SUITE")
    print("=" * 65)
    passed, total = 0, 0

    # Test 1: Math Consistency
    total += 1
    print("\n[TEST 1] Mathematical Consistency Check...")
    data = predict_simulation({"crop": "Maize", "area_ha": 2.5, "temperature": 25, "soil_moisture": 55, "soil_ph": 6.5, "annual_rainfall": 800, "nitrogen": 80})
    expected_income = round(data["yield_t_ha"] * 2.5 * data["price_per_tonne"])
    expected_roi = round(((data["season_income"] - data["input_cost"]) / data["input_cost"]) * 100) if data["input_cost"] > 0 else 0
    if abs(data["season_income"] - expected_income) <= 5 and abs(data["net_roi"] - expected_roi) <= 2:
        print("  [PASS] Income and ROI match exact accounting formulas.")
        passed += 1
    else:
        print("  [FAIL] Math mismatch.")

    # Test 2: Stress Response
    total += 1
    print("\n[TEST 2] Agronomic Sensitivity & Stress Test...")
    good = predict_simulation({"crop": "Maize", "area_ha": 1.0, "temperature": 24, "soil_moisture": 60, "soil_ph": 6.5, "annual_rainfall": 700, "nitrogen": 100, "fertilizer_level": 80, "irrigation_level": 70})
    poor = predict_simulation({"crop": "Maize", "area_ha": 1.0, "temperature": 38, "soil_moisture": 15, "soil_ph": 4.5, "annual_rainfall": 100, "nitrogen": 10})
    if (poor["yield_t_ha"] < good["yield_t_ha"]) and (poor["success_rate"] < good["success_rate"]) and (good["condition"] == "Good") and (poor["condition"] == "Poor"):
        print(f"  [PASS] Yield drops under stress from {good['yield_t_ha']} to {poor['yield_t_ha']} t/ha; Condition: Good -> Poor.")
        passed += 1
    else:
        print("  [FAIL] Stress response failed.")

    # Test 3: Condition Breakdown Bounds
    total += 1
    print("\n[TEST 3] Suitability Fit Boundary Verification...")
    fits = [good["temperature_fit"], good["ph_fit"], good["moisture_fit"], good["rainfall_fit"], good["nitrogen_fit"]]
    if all(0 <= f <= 100 for f in fits) and poor["ph_fit"] <= 20 and poor["moisture_fit"] <= 20:
        print("  [PASS] All 5 suitability fit bars are bounded in [0, 100%]. Stressed inputs are severely penalized.")
        passed += 1
    else:
        print("  [FAIL] Fit boundary error.")

    # Test 4: All 9 Crops
    total += 1
    print("\n[TEST 4] All 9 Crops Pipeline Verification...")
    crops = ["Rice", "Wheat", "Maize", "Tomato", "Cotton", "Sugarcane", "Soybean", "Groundnut", "Banana"]
    if all(predict_simulation({"crop": c, "area_ha": 1.0})["yield_t_ha"] > 0 for c in crops):
        print("  [PASS] All 9 crops processed successfully with realistic, non-negative predictions.")
        passed += 1
    else:
        print("  [FAIL] Incompatible crop prediction.")

    print("\n" + "=" * 65)
    pct = round(passed / total * 100)
    print(f"OVERALL: {passed}/{total} tests passed ({pct}%)")
    print("=" * 65)
    return passed == total

if __name__ == "__main__":
    ok = run_tests()
    sys.exit(0 if ok else 1)
