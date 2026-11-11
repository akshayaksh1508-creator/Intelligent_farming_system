import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "farmwise-super-secret-key-2026")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'farmwise.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY", "your_weatherapi_key_here")
    WEATHER_API_BASE = "http://api.weatherapi.com/v1"
    DATA_GOV_API_KEY = os.environ.get("DATA_GOV_API_KEY", "")  # free key from data.gov.in for live mandi prices
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")  # Google Gemini Vision API key for disease detection
    ESP32_DEVICE_TOKEN = os.environ.get("ESP32_DEVICE_TOKEN", "change-this-device-token")
    HARDWARE_STALE_SECONDS = int(os.environ.get("HARDWARE_STALE_SECONDS", "120"))
    APP_NAME = "Farm Wise AI"


class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
