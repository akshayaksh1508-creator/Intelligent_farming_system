"""
Farm Wise AI – Virtual Farm / Crop Simulator 3D Routes
API endpoints for ML-driven simulation predictions.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from ml_models.simulation_model import predict_simulation
from models import HardwareReading

simulation_bp = Blueprint("simulation", __name__, url_prefix="/api/simulation")

@simulation_bp.route("/predict", methods=["POST"])
def api_simulation_predict():
    """
    POST /api/simulation/predict
    Accepts JSON input with crop, area_ha, and soil/climate parameters.
    Returns ML predictions for yield, income, water, harvest duration, CO2, cost, ROI,
    condition, and condition breakdown fits.
    """
    try:
        data = request.get_json(silent=True) or {}
        if not data:
            return jsonify({"success": False, "error": "Request body must be valid JSON"}), 400

        sensor_source = "manual/default"
        if data.get("use_hardware", True):
            reading = HardwareReading.query.order_by(HardwareReading.received_at.desc()).first()
            if reading:
                age = (datetime.utcnow() - reading.received_at).total_seconds()
                if age <= current_app.config.get("HARDWARE_STALE_SECONDS", 120):
                    data.setdefault("soil_moisture", reading.soil_moisture)
                    data.setdefault("humidity", reading.humidity)
                    if reading.temperature is not None:
                        data.setdefault("temperature", reading.temperature)
                    sensor_source = "ESP32"

        result = predict_simulation(data)
        result["sensor_source"] = sensor_source
        result["inputs"] = {
            "soil_moisture": data.get("soil_moisture", 50.0),
            "humidity": data.get("humidity", 65.0),
            "temperature": data.get("temperature", 24.0),
            "pH": data.get("soil_ph", 6.5),
            "nitrogen": data.get("nitrogen", 70.0),
            "rainfall": data.get("annual_rainfall", 700.0),
        }
        return jsonify(result), 200
    except ValueError as ve:
        return jsonify({"success": False, "error": f"Invalid input: {str(ve)}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Simulation prediction failed: {str(e)}"}), 500
