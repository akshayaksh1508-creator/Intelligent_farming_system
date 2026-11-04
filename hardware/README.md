# Farm Wise AI ESP32 connection

1. Install the Arduino libraries `DHT sensor library`, `Adafruit Unified Sensor`, and `ArduinoJson`.
2. Open `esp32_farmwise.ino`.
3. Set the Wi-Fi name/password, the computer’s LAN IP in `API_URL`, and the same token as `ESP32_DEVICE_TOKEN` in the Flask environment.
4. Connect the capacitive soil sensor output to GPIO 34 and the DHT data pin to GPIO 4. Connect both sensors to 3.3V and GND.
5. Calibrate `SOIL_RAW_DRY` and `SOIL_RAW_WET` using the Serial Monitor, then flash the ESP32.
6. Start Flask and open the dashboard. The dashboard polls `/api/hardware/latest` every 10 seconds and the simulator sends the latest readings to `/api/simulation/predict`.

For a same-network setup, `API_URL` should look like:

`http://192.168.1.25:5000/api/hardware/telemetry`

The Flask computer and ESP32 must be on the same Wi-Fi network, and Windows Firewall must allow inbound TCP port 5000. For production or internet access, use HTTPS and a stronger per-device token instead of exposing the development server.
