import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SYSTEM_INSTRUCTION = """
أنت سارة، وكيلة مبيعات محترفة وودودة لمؤسستنا.
مهامك:
1. الرد على استفسارات العملاء ومساعدتهم في اختيار المنتج المناسب.
2. يدعم المتجر اللغتين العربية والإنجليزية. رد دائماً بنفس لغة العميل (إذا تحدث بالعربية رد بالعربية، وإذا تحدث بالإنجليزية رد بالإنجليزية).
3. الكتالوج الحالي المتاح للبيع:
   - المنتج الأول / Product 1: كتاب "دليل المبتدئ إلى الذكاء الاصطناعي" (PDF) 🤖📚
     * السعر / Price: 10 دنانير أردنية / 10 JOD.
   - المنتج الثاني / Product 2: قوالب هندسة الأوامر الاحترافية (Prompt Engineering) ⚡📝
     * السعر / Price: 7 دنانير أردنية / 7 JOD.
4. عندما يختار العميل منتجاً، وجهه حصراً لدفع قيمته عبر التحويل الفوري إلى محفظة أورنج موني على الرقم التالي: 00962798309654:
   - لشراء الكتاب، اطلب منه إرسال كلمة "تم التحويل للكتاب" أو "Paid Book" بالإنجليزية.
   - لشراء القوالب، اطلب منه إرسال كلمة "تم تحويل القوالب" أو "Paid Prompts" بالإنجليزية.
"""

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

def send_telegram_message(chat_id, text):
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)

def send_telegram_document(chat_id, document_url, caption):
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    requests.post(url, json={"chat_id": chat_id, "document": document_url, "caption": caption}, timeout=15)

def get_gemini_response(user_text):
    if not GEMINI_API_KEY:
        return "خطأ: مفتاح GEMINI_API_KEY غير مضاف."
    models_to_try = ["gemini-3.6-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
        "contents": [{"parts": [{"text": user_text}]}]
    }
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(url, json=payload, timeout=25)
            if res.status_code == 200:
                res_json = res.json()
                candidates = res_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "لم يتم توليد نص.")
        except Exception:
            pass
    return "عذراً، الخادم مشغول حالياً."

@app.route("/", methods=["GET"])
def index():
    return "Sarah Sales Agent with Multi-Language Support is Active!"

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json(force=True)
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"].get("text", "")

        if user_text == "/start":
            send_telegram_message(chat_id, "أهلاً بك في متجرنا الرقمي! أنا سارة، مساعدة المبيعات. كيف يمكنني خدمتك اليوم؟ 😊\nWelcome to our digital store! I am Sarah, your sales assistant. How can I help you today? 😊")
            return jsonify({"status": "ok"})

        if "تم التحويل للكتاب" in user_text or user_text == "تم التحويل" or "Paid Book" in user_text:
            book_url = "https://raw.githubusercontent.com/Mohammad1991208/my-first-project/main/AI_Guide.pdf"
            send_telegram_document(chat_id, book_url, "شكراً لتأكيد الدفع! تفضل كتاب 'دليل المبتدئ إلى الذكاء الاصطناعي'. 🤖📚\nThank you for confirming payment! Here is your AI Beginner's Guide.")
            return jsonify({"status": "ok"})

        if "تم تحويل القوالب" in user_text or "Paid Prompts" in user_text:
            prompts_url = "https://raw.githubusercontent.com/Mohammad1991208/my-first-project/main/Prompts_Guide.txt"
            send_telegram_document(chat_id, prompts_url, "شكراً لتأكيد الدفع! تفضل 'قوالب هندسة الأوامر الاحترافية'. ⚡📝\nThank you for confirming payment! Here are your Prompt Engineering templates.")
            return jsonify({"status": "ok"})

        reply_text = get_gemini_response(user_text)
        send_telegram_message(chat_id, reply_text)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
