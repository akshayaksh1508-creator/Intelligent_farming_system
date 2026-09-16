"""
Farm Wise AI – Chatbot Routes (AI Assistant)
"""

import random
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import current_user

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")

# ─── Multilingual Response Database ──────────────────────────────────────────

RESPONSES = {
    "greeting": {
        "en": "Hello! I'm Farm Wise AI Assistant 🌱. I can help you with crop recommendations, disease diagnosis, weather updates, market prices, and government schemes. How can I help you today?",
        "hi": "नमस्ते! मैं Farm Wise AI सहायक हूँ 🌱। मैं फसल अनुशंसा, रोग निदान, मौसम अपडेट, बाजार भाव और सरकारी योजनाओं में आपकी मदद कर सकता हूँ।",
        "kn": "ನಮಸ್ಕಾರ! ನಾನು Farm Wise AI ಸಹಾಯಕ 🌱. ಬೆಳೆ ಶಿಫಾರಸು, ರೋಗ ಗುರುತಿಸುವಿಕೆ, ಹವಾಮಾನ ಅಪ್‌ಡೇಟ್‌ಗಳಲ್ಲಿ ನಿಮಗೆ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ.",
        "ta": "வணக்கம்! நான் Farm Wise AI உதவியாளர் 🌱. பயிர் பரிந்துரை, நோய் கண்டறிதல் மற்றும் சந்தை விலைகளில் உதவ தயாராக இருக்கிறேன்.",
        "te": "నమస్కారం! నేను Farm Wise AI సహాయకుడు 🌱. పంట సిఫార్సు, వ్యాధి నిర్ధారణ మరియు మార్కెట్ ధరలలో సహాయం చేయగలను.",
        "mr": "नमस्कार! मी Farm Wise AI सहाय्यक आहे 🌱. पीक शिफारस, रोग निदान आणि बाजार भावांमध्ये मदत करतो.",
    },
    "crop": {
        "en": "🌾 For crop recommendation, I need to know: your soil type (loamy/sandy/clay), NPK levels, temperature, humidity, rainfall, and season (Kharif/Rabi/Zaid). You can also use our detailed AI Crop Recommendation tool at /crop for a full analysis!",
        "hi": "🌾 फसल अनुशंसा के लिए, मुझे आपकी मिट्टी का प्रकार, NPK स्तर, तापमान, नमी, वर्षा और मौसम बताएं। आप /crop पर हमारे AI उपकरण का उपयोग कर सकते हैं।",
        "kn": "🌾 ಬೆಳೆ ಶಿಫಾರಸಿಗೆ, ನಿಮ್ಮ ಮಣ್ಣಿನ ಪ್ರಕಾರ, NPK ಮಟ್ಟ, ತಾಪಮಾನ ಮತ್ತು ಋತುವಿನ ಬಗ್ಗೆ ತಿಳಿಸಿ।",
    },
    "disease": {
        "en": "🔬 To identify plant disease, please upload a clear photo of the affected leaf or plant part to our Disease Detection tool at /disease. Our AI will analyze it and provide treatment recommendations!",
        "hi": "🔬 रोग पहचान के लिए, /disease पर प्रभावित पत्ते की स्पष्ट फ़ोटो अपलोड करें। हमारा AI इसका विश्लेषण करेगा।",
        "kn": "🔬 ರೋಗ ಗುರುತಿಸಲು, /disease ನಲ್ಲಿ ಪ್ರಭಾವಿತ ಎಲೆಯ ಸ್ಪಷ್ಟ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ।",
    },
    "weather": {
        "en": "🌤️ Check real-time weather at /weather. Currently in New Delhi: 34°C, 62% humidity, partly cloudy. Rain probability: 25%. The next 7-day forecast shows mostly dry conditions with mild temperatures ideal for sowing.",
        "hi": "🌤️ वास्तविक समय मौसम /weather पर देखें। नई दिल्ली में अभी: 34°C, 62% आर्द्रता, आंशिक रूप से बादल। बारिश की संभावना: 25%।",
        "kn": "🌤️ ನೈಜ-ಸಮಯ ಹವಾಮಾನ /weather ನಲ್ಲಿ ನೋಡಿ।",
    },
    "market": {
        "en": "📈 Today's market highlights:\n• Tomato: ₹2,450/quintal (+12.5% ↑)\n• Rice: ₹2,183/quintal (+2.1% ↑)\n• Wheat: ₹2,275/quintal (-0.5% ↓)\n• Cotton: ₹6,620/quintal (+3.2% ↑)\nVisit /marketplace for detailed price trends and charts!",
        "hi": "📈 आज के बाजार भाव:\n• टमाटर: ₹2,450/क्विंटल (+12.5% ↑)\n• चावल: ₹2,183/क्विंटल\n• गेहूं: ₹2,275/क्विंटल\nविस्तृत भाव के लिए /marketplace देखें।",
        "kn": "📈 ಇಂದಿನ ಮಾರುಕಟ್ಟೆ ಭಾವ:\n• ಟೊಮ್ಯಾಟೊ: ₹2,450/ಕ್ವಿಂಟಾಲ್\n• ಅಕ್ಕಿ: ₹2,183/ಕ್ವಿಂಟಾಲ್",
    },
    "scheme": {
        "en": "🏛️ Key Government Schemes for Farmers:\n1. **PM-KISAN** – ₹6,000/year direct income support\n2. **PMFBY** – Pradhan Mantri Fasal Bima Yojana (crop insurance)\n3. **KCC** – Kisan Credit Card (low interest credit)\n4. **eNAM** – Electronic National Agriculture Market\n5. **Soil Health Card Scheme** – Free soil testing\n\nVisit /schemes for eligibility and application details!",
        "hi": "🏛️ प्रमुख सरकारी योजनाएं:\n1. PM-KISAN – ₹6,000/वर्ष आय सहायता\n2. PMFBY – फसल बीमा योजना\n3. KCC – किसान क्रेडिट कार्ड\n/schemes पर अधिक जानकारी देखें।",
        "kn": "🏛️ ಪ್ರಮುಖ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು:\n1. PM-KISAN – ₹6,000/ವರ್ಷ ಆದಾಯ ಬೆಂಬಲ\n2. PMFBY – ಬೆಳೆ ವಿಮೆ",
    },
    "fertilizer": {
        "en": "🧪 Fertilizer Guide:\n• **Nitrogen (N)**: Promotes leaf growth – Use Urea (46% N)\n• **Phosphorus (P)**: Root development – Use DAP (18:46:00)\n• **Potassium (K)**: Fruit quality – Use MOP (0:0:60)\n• Apply based on soil test report for best results. Always split nitrogen application into 3 doses.",
        "hi": "🧪 उर्वरक मार्गदर्शिका:\n• नाइट्रोजन (N) – यूरिया का उपयोग करें\n• फास्फोरस (P) – DAP का उपयोग करें\n• पोटेशियम (K) – MOP का उपयोग करें",
        "kn": "🧪 ಗೊಬ್ಬರ ಮಾರ್ಗದರ್ಶಿ:\n• ಸಾರಜನಕ (N) – ಯೂರಿಯಾ ಬಳಸಿ\n• ರಂಜಕ (P) – DAP ಬಳಸಿ",
    },
    "irrigation": {
        "en": "💧 Smart Irrigation Tips:\n• Drip irrigation saves 50-70% water vs flood irrigation\n• Irrigate in early morning or evening to minimize evaporation\n• Use soil moisture sensors to optimize scheduling\n• Mulching reduces water needs by 30%\n• Sprinkler systems suit most field crops",
        "hi": "💧 सिंचाई सुझाव:\n• ड्रिप सिंचाई 50-70% पानी बचाती है\n• सुबह या शाम को सिंचाई करें\n• मल्चिंग से 30% पानी की बचत होती है",
        "kn": "💧 ನೀರಾವರಿ ಸಲಹೆಗಳು:\n• ಡ್ರಿಪ್ ನೀರಾವರಿ 50-70% ನೀರು ಉಳಿಸುತ್ತದೆ\n• ಬೆಳಿಗ್ಗೆ ಅಥವಾ ಸಂಜೆ ನೀರಾವರಿ ಮಾಡಿ",
    },
    "default": {
        "en": "I understand you're asking about farming. Could you be more specific? I can help with:\n🌾 **Crop Recommendation** – Best crops for your conditions\n🔬 **Disease Detection** – Identify plant diseases\n🌤️ **Weather** – Forecast and alerts\n📈 **Market Prices** – Latest crop prices\n🏛️ **Government Schemes** – Subsidies and support\n💧 **Irrigation** – Water management tips\n\nType any of these topics to get started!",
        "hi": "मैं समझ गया कि आप खेती के बारे में पूछ रहे हैं। कृपया अधिक विशिष्ट बताएं।",
        "kn": "ನೀವು ಕೃಷಿ ಬಗ್ಗೆ ಕೇಳುತ್ತಿದ್ದೀರಿ. ದಯವಿಟ್ಟು ಹೆಚ್ಚು ನಿರ್ದಿಷ್ಟವಾಗಿ ತಿಳಿಸಿ.",
    },
}


def get_intent(message):
    """Simple keyword-based intent detection."""
    msg = message.lower()
    if any(w in msg for w in ["hi", "hello", "namaste", "hey", "ಹಲೋ", "नमस्ते"]):
        return "greeting"
    if any(w in msg for w in ["crop", "grow", "plant", "sow", "seed", "फसल", "ಬೆಳೆ", "పంట"]):
        return "crop"
    if any(w in msg for w in ["disease", "sick", "pest", "rot", "blight", "virus", "रोग", "ರೋಗ"]):
        return "disease"
    if any(w in msg for w in ["weather", "rain", "temperature", "forecast", "climate", "मौसम", "ಹವಾಮಾನ"]):
        return "weather"
    if any(w in msg for w in ["price", "market", "rate", "sell", "profit", "भाव", "ಮಾರು", "ధర"]):
        return "market"
    if any(w in msg for w in ["scheme", "government", "subsidy", "yojana", "loan", "योजना", "ಯೋಜನೆ"]):
        return "scheme"
    if any(w in msg for w in ["fertilizer", "npk", "urea", "dap", "compost", "उर्वरक", "ಗೊಬ್ಬರ"]):
        return "fertilizer"
    if any(w in msg for w in ["water", "irrigation", "drip", "sprinkler", "सिंचाई", "ನೀರಾವರಿ"]):
        return "irrigation"
    return "default"


def detect_language(message):
    """Detect language from character set."""
    if any('\u0900' <= c <= '\u097F' for c in message):
        return "hi"
    if any('\u0C80' <= c <= '\u0CFF' for c in message):
        return "kn"
    if any('\u0B80' <= c <= '\u0BFF' for c in message):
        return "ta"
    if any('\u0C00' <= c <= '\u0C7F' for c in message):
        return "te"
    return "en"


@chatbot_bp.route("/")
def index():
    return render_template("chatbot/index.html")


@chatbot_bp.route("/api/message", methods=["POST"])
def handle_message():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    lang = data.get("language", "en")

    if not message:
        return jsonify({"error": "Empty message"}), 400

    # Detect language if not specified
    detected_lang = detect_language(message)
    if detected_lang != "en":
        lang = detected_lang

    intent = get_intent(message)
    lang_responses = RESPONSES.get(intent, RESPONSES["default"])
    response_text = lang_responses.get(lang, lang_responses.get("en", "I can help you with farming questions!"))

    return jsonify({
        "response": response_text,
        "intent": intent,
        "language": lang,
        "timestamp": __import__("datetime").datetime.now().strftime("%H:%M"),
    })


@chatbot_bp.route("/api/quick-questions")
def quick_questions():
    questions = [
        "What crop should I grow this season?",
        "How to identify tomato blight?",
        "What's today's rice market price?",
        "Tell me about PM-KISAN scheme",
        "Best irrigation method for small farm?",
        "How to improve soil fertility?",
    ]
    return jsonify({"questions": questions})
