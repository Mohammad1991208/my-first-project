import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# تعليمات النظام والكتالوج المخصص لـ سارة
SYSTEM_INSTRUCTION = """
أنت سارة، وكيلة مبيعات محترفة وودودة لمؤسستنا.
مهامك:
1. الرد على استفسارات العملاء بناءً على الكتالوج والمنتجات والدورات المتاحة.
2. مساعدة العملاء في اختيار المنتج أو الدورة المناسبة.
3. توجيه العميل لرابط الشراء عند رغبته في الطلب.
"""

# المتغيرات الأساسية
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

def send_telegram_message(chat_id, text):
    """إرسال رد إلى مستخدم تلجرام"""
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending telegram message: {e}")

def get_gemini_response(user_text):
    """الترابط المباشر مع API الخاص بـ Gemini باستخدام النموذج المعتمد gemini-2.5-flash"""
    if not GEMINI_API_KEY:
        return "خطأ: مفتاح GEMINI_API_KEY غير مضاف في Variables."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}]
        },
        "contents": [
            {
                "parts": [{"text": user_text}]
            }
        ]
    }
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        res_json = res.json()
        
        if res.status_code == 200:
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "لم يتم توليد نص.")
            return "عذراً، لم أتمكن من إعداد الإجابة."
        else:
            error_msg = res_json.get("error", {}).get("message", "خطأ غير معروف")
            print(f"Gemini API Error: {res.status_code} - {error_msg}")
            return f"عذراً، حدث خطأ في النظام: {error_msg}"
    except Exception as e:
        print(f"Exception calling Gemini: {e}")
        return "عذراً، حدث خطأ أثناء الاتصال بالخادم."

@app.route("/", methods=["GET"])
def index():
    return "Sarah Sales Agent is Active!"

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json(force=True)
    
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"].get("text", "")

        # الأمر الترحيبي
        if user_text == "/start":
            send_telegram_message(chat_id, "أهلاً بك! أنا سارة، كيف يمكنني مساعدتك اليوم؟ 😊")
            return jsonify({"status": "ok"})

        # التفاعل مع الذكاء الاصطناعي
        reply_text = get_gemini_response(user_text)
        send_telegram_message(chat_id, reply_text)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
