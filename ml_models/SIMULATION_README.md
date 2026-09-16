# Stage 1 — Virtual Farm Simulation Model

This model predicts crop growth percentage from the fields already present in the Crop Simulator 3D UI: crop, simulation day, soil pH, soil moisture, nitrogen, temperature, rainfall and a prototype fertilizer level.

### Files
- `simulation_data/simulation_prototype_dataset.csv` — synthetic training data
- `train_simulation_model.py` — retraining script
- `simulation_growth_model.joblib` — trained prototype model
- `simulation_model.py` — prediction wrapper
- `simulation_model_schema.json` — model feature schema

### Flask API
`POST /api/simulation/predict`

The model is for Stage 1 prototyping only. When hardware is ready, retrain/calibrate it using real sensor observations.
