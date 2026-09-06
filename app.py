import os
import asyncio
from flask import Flask, request, jsonify
from google import genai
import requests

app = Flask(__name__)

# تعليمات النظام لـ سارة
SYSTEM_INSTRUCTION = """
أنت سارة، وكيلة مبيعات محترفة وودودة لمؤسستنا.
مهامك:
1. الرد على استفسارات العملاء بناءً على الكتالوج والمنتجات والدورات المتاحة.
2. مساعدة العملاء في اختيار المنتج أو الدورة المناسبة.
3. توجيه العميل لرابط الشراء عند رغبته في الطلب.
"""

# جلب المتغيرات
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# إعداد عميل Gemini
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def send_telegram_message(chat_id, text):
    """إرسال رد إلى مستخدم تلجرام مباشرة عبر HTTP API"""
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
        print(f"Error sending message: {e}")

@app.route("/", methods=["GET"])
def index():
    return "Sarah Sales Agent is active!"

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json(force=True)
    
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"].get("text", "")

        # التعامل مع أمر البداية
        if user_text == "/start":
            send_telegram_message(chat_id, "أهلاً بك! أنا سارة، كيف يمكنني مساعدتك اليوم؟ 😊")
            return jsonify({"status": "ok"})

        # معالجة النصوص عبر Gemini
        if client:
            try:
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=user_text,
                    config={"system_instruction": SYSTEM_INSTRUCTION}
                )
                reply_text = response.text if response.text else "عذراً، لم أتمكن من إعداد الإجابة."
            except Exception as e:
                print(f"Gemini API Error: {e}")
                reply_text = "عذراً، حدث خطأ أثناء معالجة الطلب."
        else:
            reply_text = "خطأ: لم يتم ضبط مفتاح Gemini API."

        send_telegram_message(chat_id, reply_text)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
