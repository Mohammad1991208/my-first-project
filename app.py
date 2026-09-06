import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# تعليمات النظام والكتالوج المحدث لـ سارة
SYSTEM_INSTRUCTION = """
أنت سارة، وكيلة مبيعات محترفة وودودة لمؤسستنا.
مهامك:
1. الرد على استفسارات العملاء ومساعدتهم في اختيار المنتج المناسب.
2. الكتالوج الحالي المتاح للبيع:
   - كتاب: "دليل المبتدئ إلى الذكاء الاصطناعي" 🤖📚
   - الوصف: دليل مصغر وعملي لفهم أساسيات الذكاء الاصطناعي وكيفية استخدام أدواته الذكية لمضاعفة إنتاجيتك في العمل والحياة.
   - السعر: 10 دنانير أردنية.
3. عندما يبدي العميل رغبته بالشراء، وجهه حصراً لدفع القيمة عبر التحويل الفوري إلى محفظة أورنج موني على الرقم التالي: 00962798309654، واطلب منه إرسال كلمة "تم التحويل" لإرسال الكتاب له فوراً.
"""

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

def send_telegram_message(chat_id, text):
    """إرسال رد نصي إلى مستخدم تلجرام"""
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

def send_telegram_document(chat_id, document_url, caption):
    """إرسال ملف الكتاب تلقائياً إلى مستخدم تلجرام"""
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    payload = {
        "chat_id": chat_id,
        "document": document_url,
        "caption": caption
    }
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"Error sending telegram document: {e}")

def get_gemini_response(user_text):
    """الاتصال بـ Gemini للرد على استفسارات العملاء"""
    if not GEMINI_API_KEY:
        return "خطأ: مفتاح GEMINI_API_KEY غير مضاف في Variables."
    
    models_to_try = ["gemini-3.6-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]
    
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
    
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(url, json=payload, timeout=25)
            res_json = res.json()
            
            if res.status_code == 200:
                candidates = res_json.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "لم يتم توليد نص.")
            else:
                error_msg = res_json.get("error", {}).get("message", "خطأ غير معروف")
                print(f"Model {model_name} failed: {error_msg}")
        except Exception as e:
            print(f"Exception calling model {model_name}: {e}")
            
    return "عذراً، الخادم مشغول حالياً. يرجى إعادة محاولة إرسال الرسالة."

@app.route("/", methods=["GET"])
def index():
    return "Sarah Sales Agent is Active!"

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json(force=True)
    
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"].get("text", "")

        if user_text == "/start":
            send_telegram_message(chat_id, "أهلاً بك! أنا سارة، وكيلة المبيعات. كيف يمكنني مساعدتك اليوم؟ 😊")
            return jsonify({"status": "ok"})

        # التحقق إذا كتب العميل كلمة التأكيد لإرسال الكتاب آلياً
        if "تم التحويل" in user_text or "إيصال" in user_text:
            book_url = "https://raw.githubusercontent.com/Mohammad1991208/my-first-project/main/AI_Guide.pdf"
            send_telegram_document(chat_id, book_url, "شكراً لتأكيد الدفع! تفضل كتاب 'دليل المبتدئ إلى الذكاء الاصطناعي'. نتمنى لك قراءة ممتعة ومفيدة 🤖📚")
            return jsonify({"status": "ok"})

        # الرد الطبيعي عبر ذكاء سارة
        reply_text = get_gemini_response(user_text)
        send_telegram_message(chat_id, reply_text)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
