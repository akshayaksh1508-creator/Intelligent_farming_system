# Farm Wise AI — Farmer Mobile App

React Native (Expo) app for farmers. It talks to the same Flask REST API as the
website, so crop recommendations, disease scans, weather, market prices and the
ESP32 sensor readings all work from a phone.

## What it does

- **Home** — weather forecast + live ESP32 farm sensor card (polled every 10 s)
- **Crop** — automatic AI crop recommendation via `GET /api/crop/auto`: values are
  collected from the ESP32 sensor (temperature, humidity), the weather service,
  the calendar season, and soil-test defaults — no manual inputs
- **Scan** — photograph a leaf and the CNN runs **on the phone** (TFLite
  backbone + bundled disease heads and treatment texts), the same prediction
  as `POST /api/disease/analyze` — no server, no internet needed.
- **Market** — today's mandi prices and the farm supply marketplace.
- **Settings** — server address, connection test, account info, logout.

## Run on a phone (Expo Go)

1. Start the Flask server on your computer:

   ```
   cd D:\Akshay\Documents\scratch\farm-wise-ai
   py app.py
   ```

   Keep the computer and the phone on the **same Wi-Fi network**.

2. Allow inbound TCP 5000 through Windows Firewall (if not already allowed):

   ```
   netsh advfirewall firewall add rule name="FarmWise Flask 5000" dir=in action=allow protocol=TCP localport=5000
   ```

3. Start Expo in the mobile folder:

   ```
   cd D:\Akshay\Documents\scratch\farm-wise-ai\mobile
   npx expo start
   ```

4. Install **Expo Go** on the phone and scan the QR code.

5. The app auto-detects the server address from the Expo connection (it uses the
   Metro host IP with port 5000). If that fails, tap **Edit** on the login
   screen (or Settings → Server address) and enter
   `http://<YOUR-PC-LAN-IP>:5000`, e.g. `http://192.168.1.25:5000`.

   Find the PC's LAN IP with `ipconfig` (look for the Wi-Fi adapter's IPv4 address).

Login with a farmer account (e.g. `ramesh@example.com` / `farmer123`, or create
one in the app). Farmer accounts may need admin approval
(`admin@farmwise.ai` / `admin123`) before login works.

## Build an installable APK (EAS)

The app uses only Expo Go-compatible packages, so you can also ship it as an
APK without ejecting. Native configuration (image picker permissions, cleartext
HTTP for the LAN server) is already in `app.json`.

```
cd D:\Akshay\Documents\scratch\farm-wise-ai\mobile
npm install -g eas-cli
eas login
eas build --platform android --profile development
```

The development profile produces a development client (requires the
`expo-dev-client` package) for testing; add it first with
`npx expo install expo-dev-client`. For a plain shareable APK, add a `preview`
profile in `eas.json` (`"preview": { "distribution": "internal" }`) and run
`eas build --platform android --profile preview`.

The APK expects the Flask server at a reachable address — set it in
Settings → Server address the first time you open the app.

## Project layout

- `App.tsx` — auth gate + bottom-tab navigation (Home / Crop / Scan / Market / Settings)
- `src/api.ts` — fetch wrapper; base URL comes from AsyncStorage, defaulting to
  the Expo host IP on port 5000
- `src/context/AuthContext.tsx` — login/register/logout against the Flask
  session-cookie API
- `src/screens/*` — one screen per tab
- `src/components/ui.tsx` — shared card/button/field/picker components
