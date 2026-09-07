import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SYSTEM_INSTRUCTION = """
أنت سارة، وكيلة مبيعات محترفة وودودة لمؤسستنا.
مهامك:
1. الرد على استفسارات العملاء ومساعدتهم في اختيار المنتج المناسب باللغتين العربية والإنجليزية.
2. الكتالوج الحالي المتاح للبيع:
   - المنتج الأول / Product 1: كتاب "دليل المبتدئ إلى الذكاء الاصطناعي" (PDF) 🤖📚 (السعر: 10 دنانير / 10 JOD)
   - المنتج الثاني / Product 2: قوالب هندسة الأوامر الاحترافية (Prompt Engineering) ⚡📝 (السعر: 7 دنانير / 7 JOD)
3. عندما يختار العميل منتجاً، وجهه حصراً لدفع قيمته عبر التحويل الفوري إلى محفظة أورنج موني على الرقم التالي: 00962798309654:
   - لشراء الكتاب، اطلب منه إرسال كلمة "تم التحويل للكتاب" أو "Paid Book".
   - لشراء القوالب، اطلب منه إرسال كلمة "تم تحويل القوالب" أو "Paid Prompts".
"""

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID") # ضع هنا معرف تليجرام الخاص بك (Chat ID) لكي تصلك الإشعارات

# عداد بسيط لتتبع المبيعات مؤقتاً
sales_stats = {
    "books_sold": 0,
    "prompts_sold": 0
}

def send_telegram_message(chat_id, text, reply_markup=None):
    if not TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload, timeout=10)

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
    return "Sarah Sales Agent - Pro Edition is Active!"

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json(force=True)
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        user_text = message.get("text", "")
        user_name = message["from"].get("first_name", "عميل")

        # لوحة الأزرار الثابتة التفاعلية أسفل الشاشة
        main_keyboard = {
            "keyboard": [
                [{"text": "📚 عرض المنتجات | Products"}, {"text": "💳 طرق الدفع | Payment"}],
                [{"text": "☎️ تواصل معنا | Contact"}]
            ],
            "resize_keyboard": True
        }

        if user_text == "/start":
            welcome_msg = (
                "أهلاً بك في متجرنا الرقمي الاحترافي! أنا سارة، مساعدة المبيعات. 😊\n"
                "Welcome to our professional digital store! I am Sarah, your sales assistant.\n\n"
                "اختر من الأزرار بالأسفل أو اسألني عما تريده مباشرة:"
            )
            send_telegram_message(chat_id, welcome_msg, reply_markup=main_keyboard)
            return jsonify({"status": "ok"})

        # أمر خاص للإحصائيات للمدير
        if user_text == "/stats":
            stats_text = f"📊 إحصائيات المبيعات الحالية:\n- كتب تم بيعها: {sales_stats['books_sold']}\n- قوالب تم بيعها: {sales_stats['prompts_sold']}"
            send_telegram_message(chat_id, stats_text)
            return jsonify({"status": "ok"})

        # الردود السريعة للأزرار الثابتة
        if "عرض المنتجات" in user_text or "Products" in user_text:
            products_msg = (
                "📦 الكتالوج المتاح:\n"
                "1️⃣ كتاب دليل الذكاء الاصطناعي (10 JOD)\n"
                "2️⃣ قوالب هندسة الأوامر (7 JOD)\n\n"
                "لطلب الكتاب أرسل: تم التحويل للكتاب / Paid Book\n"
                "لطلب القوالب أرسل: تم تحويل القوالب / Paid Prompts"
            )
            send_telegram_message(chat_id, products_msg, reply_markup=main_keyboard)
            return jsonify({"status": "ok"})

        if "طرق الدفع" in user_text or "Payment" in user_text:
            pay_msg = "💳 يتم الدفع عبر التحويل الفوري لمحفظة أورنج موني على الرقم:\n00962798309654\nثم أرسل تأكيد الدفع للحصول على الملف فوراً."
            send_telegram_message(chat_id, pay_msg, reply_markup=main_keyboard)
            return jsonify({"status": "ok"})

        if "تواصل معنا" in user_text or "Contact" in user_text:
            contact_msg = "💬 نحن دائماً في خدمتك! يمكنك إرسال استفسارك هنا وسأرد عليك فوراً."
            send_telegram_message(chat_id, contact_msg, reply_markup=main_keyboard)
            return jsonify({"status": "ok"})

        # معالجة شراء الكتاب
        if "تم التحويل للكتاب" in user_text or user_text == "تم التحويل" or "Paid Book" in user_text:
            sales_stats["books_sold"] += 1
            book_url = "https://raw.githubusercontent.com/Mohammad1991208/my-first-project/main/AI_Guide.pdf"
            send_telegram_document(chat_id, book_url, "شكراً لتأكيد الدفع! تفضل كتاب 'دليل المبتدئ إلى الذكاء الاصطناعي'. 🤖📚")
            
            # إشعار المدير إذا تم ضبط رقمك
            if ADMIN_CHAT_ID:
                send_telegram_message(ADMIN_CHAT_ID, f"🔔 تنبيه مبيعات: العميل ({user_name}) قام بطلب وتنزيل كتاب الذكاء الاصطناعي!")
            return jsonify({"status": "ok"})

        # معالجة شراء القوالب
        if "تم تحويل القوالب" in user_text or "Paid Prompts" in user_text:
            sales_stats["prompts_sold"] += 1
            prompts_url = "https://raw.githubusercontent.com/Mohammad1991208/my-first-project/main/Prompts_Guide.txt"
            send_telegram_document(chat_id, prompts_url, "شكراً لتأكيد الدفع! تفضل 'قوالب هندسة الأوامر الاحترافية'. ⚡📝")
            
            # إشعار المدير
            if ADMIN_CHAT_ID:
                send_telegram_message(ADMIN_CHAT_ID, f"🔔 تنبيه مبيعات: العميل ({user_name}) قام بطلب وتنزيل قوالب هندسة الأوامر!")
            return jsonify({"status": "ok"})

        # المحادثة الذكية عبر جيميني للبقية
        reply_text = get_gemini_response(user_text)
        send_telegram_message(chat_id, reply_text, reply_markup=main_keyboard)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
