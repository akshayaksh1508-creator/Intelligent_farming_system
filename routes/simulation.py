"""
Farm Wise AI – Virtual Farm / Crop Simulator 3D Routes
API endpoints for ML-driven simulation predictions.
"""

from flask import Blueprint, request, jsonify
from ml_models.simulation_model import predict_simulation

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

        result = predict_simulation(data)
        return jsonify(result), 200
    except ValueError as ve:
        return jsonify({"success": False, "error": f"Invalid input: {str(ve)}"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Simulation prediction failed: {str(e)}"}), 500
