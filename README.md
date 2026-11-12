# Intelligent Farming System– AI-Powered Smart Agriculture Platform

A complete full-stack smart agriculture platform built using **Python (Flask)** for backend REST APIs, **HTML5**, **CSS3**, and **Vanilla JavaScript (ES6)** for the frontend (no Jinja template engine syntax).

Designed with a modern SaaS UI matching the premium Emerald Green & White glassmorphism aesthetic.

---

## 🚀 Key Features

1. **AI Crop Recommendation**: Scikit-Learn Random Forest model trained on soil nutrient (NPK), climate, pH, and season parameters.
2. **Plant Disease Detection**: Image analysis for plant leaves with biological, chemical medicine, and organic remedies.
3. **Weather Intelligence**: Live weather integration (WeatherAPI.com with demo fallback), 7-day forecast, humidity, and rainfall alerts.
4. **Commodity Market Prices**: Live market price tracker across Indian APMCs with trend indicators (+/- %).
5. **Agricultural Marketplace**: Products catalogue for seeds, fertilizers, organic compost, irrigation kits, and machinery.
6. **Carbon Farming Advisor**: Carbon credit calculator for sustainable agricultural practices.
7. **Government Schemes Directory**: Overview of PM-KISAN, PMFBY, KCC, and Soil Health Card schemes.
8. **Interactive AI Chatbot**: Floating assistant answering crop, disease, weather, and market queries.
9. **SaaS Dashboard**: Live metrics, Chart.js yield & profit forecasts, market price tables, and quick action cards.

---

## 🛠️ Architecture & Tech Stack

- **Location**: `D:\Akshay\Documents\scratch\farm-wise-ai`
- **Backend**: Python 3.10+, Flask REST API
- **Frontend**: Pure HTML5, CSS3 (Glassmorphism, Inter typography), Vanilla JavaScript ES6 (Fetch API)
- **Database**: SQLite (SQLAlchemy ORM)
- **Machine Learning**: Scikit-Learn (Random Forest Classifier), OpenCV, Pillow
- **Hardware IoT**: ESP32 telemetry over Wi-Fi, capacitive soil-moisture sensor, DHT11/DHT22

---

## 🏃 Running the Application

```bash
cd D:\Akshay\Documents\scratch\farm-wise-ai

# Install dependencies
pip install -r requirements.txt

# Run the Flask Server
python app.py
```

Then open your browser and visit:
**http://127.0.0.1:5000**

## 🔌 ESP32 Sensor Connection

The active dashboard reads the latest ESP32 values automatically. The device code is in
`hardware/esp32_farmwise.ino` and the wiring/setup steps are in `hardware/README.md`.

Set the same device token for Flask and the ESP32 before starting the server:

```powershell
$env:ESP32_DEVICE_TOKEN = "use-a-long-random-token"
python app.py
```

The ESP32 sends readings to `POST /api/hardware/telemetry`. The website polls
`GET /api/hardware/latest`, and the simulator uses live soil moisture, humidity, and
temperature when the latest reading is less than two minutes old. pH, nitrogen, and
rainfall still use documented defaults because those sensors are not connected yet.

---

## 🔑 Demo Login

- **Email**: `ramesh@example.com`
- **Password**: `farmer123`

---

## 🔬 Real AI disease information (recommended)

When a disease is detected, Farm Wise AI asks **Google Gemini** for the real
treatment information — accurate symptoms, chemical treatment with dosages,
medicine names available in India, organic remedies and prevention — instead
of generic template text. Without a key the app still works, falling back to
the built-in agronomic database.

Get a free API key (no credit card needed for the free tier) at
https://aistudio.google.com/apikey, then set it before starting the server:

```powershell
$env:GEMINI_API_KEY = "your-key-here"
python app.py
```

Detection pipeline: the CNN classifies the disease from the photo → Gemini
writes the treatment info → built-in agronomic database as final fallback.
The result includes `diagnosis_source` (`gemini_vision`, `gemini_advisory`,
or `cnn_agronomic`).

To also make the **mobile app's on-device results** show real AI information,
regenerate its bundled advisory file once with your key:

```powershell
$env:GEMINI_API_KEY = "your-key-here"
python disease_detection/generate_advisory_bundle.py
```

