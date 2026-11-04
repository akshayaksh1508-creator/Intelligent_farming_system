/*
  Farm Wise AI ESP32 sensor node

  Hardware:
    - Capacitive soil-moisture sensor on GPIO 34 (ADC input)
    - DHT11 or DHT22 on GPIO 4

  Arduino IDE libraries:
    - DHT sensor library by Adafruit
    - Adafruit Unified Sensor
    - ArduinoJson

  Set WIFI_SSID, WIFI_PASSWORD, API_URL and DEVICE_TOKEN before flashing.
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

#define SOIL_PIN 34
#define DHT_PIN 4
#define DHT_TYPE DHT22       // Change to DHT11 if that is your sensor

const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* API_URL = "http://YOUR_COMPUTER_IP:5000/api/hardware/telemetry";
const char* DEVICE_TOKEN = "change-this-device-token";
const char* DEVICE_ID = "esp32-farm-01";

// Calibrate these two values for your particular sensor.
// Read raw soil values in Serial Monitor when the probe is dry and wet.
const int SOIL_RAW_DRY = 3000;
const int SOIL_RAW_WET = 1200;

const unsigned long SEND_INTERVAL_MS = 30000;
unsigned long lastSend = 0;
DHT dht(DHT_PIN, DHT_TYPE);

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  unsigned long started = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - started < 20000) {
    delay(500);
    Serial.print('.');
  }
  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WiFi connection failed; will retry.");
  }
}

float soilMoisturePercent() {
  int raw = analogRead(SOIL_PIN);
  float pct = 100.0f * (SOIL_RAW_DRY - raw) / float(SOIL_RAW_DRY - SOIL_RAW_WET);
  return constrain(pct, 0.0f, 100.0f);
}

void sendReading() {
  if (WiFi.status() != WL_CONNECTED) return;

  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  if (isnan(humidity)) {
    Serial.println("DHT humidity read failed; skipping this upload.");
    return;
  }

  StaticJsonDocument<256> payload;
  payload["device_id"] = DEVICE_ID;
  payload["soil_moisture"] = round(soilMoisturePercent() * 10.0f) / 10.0f;
  payload["humidity"] = round(humidity * 10.0f) / 10.0f;
  if (!isnan(temperature)) payload["temperature"] = round(temperature * 10.0f) / 10.0f;

  String body;
  serializeJson(payload, body);

  HTTPClient http;
  http.begin(API_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", DEVICE_TOKEN);
  int status = http.POST(body);
  Serial.printf("Telemetry HTTP status: %d\n", status);
  if (status > 0) Serial.println(http.getString());
  http.end();
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  dht.begin();
  connectWiFi();
}

void loop() {
  connectWiFi();
  if (millis() - lastSend >= SEND_INTERVAL_MS || lastSend == 0) {
    lastSend = millis();
    sendReading();
  }
  delay(250);
}
