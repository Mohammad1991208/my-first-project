import os
import sqlite3
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
   - اطلب منه إرسال صورة إيصال التحويل (Screenshot) مباشرة هنا بعد إتمام الدفع ليحصل على طلبه فوراً.
"""

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

# إعداد قاعدة البيانات الدائمة SQLite
DB_NAME = "store_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # جدول لتسجيل العمليات والمبيعات الدائمة
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            user_name TEXT,
            product_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# تشغيل إنشاء الجدول عند بدء التطبيق
init_db()

def log_sale(user_id, user_name, product_type):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sales (user_id, user_name, product_type) VALUES (?, ?, ?)", 
                   (str(user_id), user_name, product_type))
    conn.commit()
    conn.close()

def get_total_sales():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_type, COUNT(*) FROM sales GROUP BY product_type")
    results = cursor.fetchall()
    conn.close()
    
    stats = {"book": 0, "prompts": 0}
    for prod, count in results:
        if prod == "book":
            stats["book"] = count
        elif prod == "prompts":
            stats["prompts"] = count
    return stats

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

def get_gemini_response(user_text, image_bytes=None):
    if not GEMINI_API_KEY:
        return "خطأ: مفتاح GEMINI_API_KEY غير مضاف."
    
    models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro"]
    
    if image_bytes:
        import base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "contents": [{
                "parts": [
                    {"text": "هذه صورة إيصال تحويل مالي لمحفظة أورنج موني. هل هذه الصورة تبدو كإيصال تحويل مالي صحيح؟ أجب بكلمة 'نعم' أو 'لا' فقط."},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }]
        }
    else:
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
    return "Sarah Sales Agent - Database Pro Edition is Active!"

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    data = request.get_json(force=True)
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        user_text = message.get("text", "")
        user_name = message["from"].get("first_name", "عميل")

        main_keyboard = {
            "keyboard": [
                [{"text": "📚 عرض المنتجات | Products"}, {"text": "💳 طرق الدفع | Payment"}],
                [{"text": "☎️ تواصل معنا | Contact"}]
            ],
            "resize_keyboard": True
        }

        if user_text == "/start":
            welcome_msg = (
                "أهلاً بك في متجرنا الرقمي! أنا سارة، مساعدة المبيعات. 😊\n"
                "Welcome to our digital store! I am Sarah, your sales assistant.\n\n"
                "اختر من الأزرار بالأسفل أو اسألني عما تريده:"
            )
            send_telegram_message(chat_id, welcome_msg, reply_markup=main_keyboard)
            return jsonify({"status": "ok"})

        if user_text == "/stats":
            stats = get_total_sales()
            stats_text = f"📊 إحصائيات المبيعات من قاعدة البيانات الدائمة:\n- الكتب المباعة: {stats['book']}\n- القوالب المباعة: {stats['prompts']}"
            send_telegram_message(chat_id, stats_text)
            return jsonify({"status": "ok"})

        if "عرض المنتجات" in user_text or "Products" in user_text:
            products_msg = (
                "📦 الكتالوج المتاح:\n"
                "1️⃣ كتاب دليل الذكاء الاصطناعي (10 JOD)\n"
                "2️⃣ قوالب هندسة الأوامر (7 JOD)\n\n"
                "بعد التحويل لأورنج موني، أرسل صورة الإيصال هنا وسأتأكد منها وأرسل لك ملفك فوراً! 📸"
            )
            send_telegram_message(chat_id, products_msg, reply_markup=main_keyboard)
            return jsonify({"status": "ok"})

        if "طرق الدفع" in user_text or "Payment" in user_text:
            pay_msg = "💳 يتم الدفع عبر التحويل الفوري لمحفظة أورنج موني على الرقم:\n00962798309654\nثم أرسل صورة الإيصال للحصول على الملف فوراً."
            send_telegram_message(chat_id, pay_msg, reply_markup=main_keyboard)
            return jsonify({"status": "ok"})

        if "تواصل معنا" in user_text or "Contact" in user_text:
            contact_msg = "💬 نحن دائماً في خدمتك! أرسل استفسارك وسأرد عليك فوراً."
            send_telegram_message(chat_id, contact_msg, reply_markup=main_keyboard)
            return jsonify({"status": "ok"})

        # فحص إيصالات الدفع بالذكاء الاصطناعي مع حفظ المبيع في قاعدة البيانات
        if "photo" in message:
            photo_list = message["photo"]
            file_id = photo_list[-1]["file_id"]
            
            file_info_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile?file_id={file_id}"
            info_res = requests.get(file_info_url).json()
            if info_res.get("ok"):
                file_path = info_res["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
                img_data = requests.get(download_url).content
                
                ai_verdict = get_gemini_response("", image_bytes=img_data)
                
                if "نعم" in ai_verdict or "Yes" in ai_verdict:
                    # حفظ عملية بيع الكتاب في قاعدة البيانات كافتراضي
                    log_sale(chat_id, user_name, "book")
                    
                    book_url = "https://raw.githubusercontent.com/Mohammad1991208/my-first-project/main/AI_Guide.pdf"
                    send_telegram_document(chat_id, book_url, "✅ تم التحقق من الإيصال بنجاح وحفظ سجلك في النظام! تفضل كتابك. 🤖📚")
                    
                    if ADMIN_CHAT_ID:
                        send_telegram_message(ADMIN_CHAT_ID, f"🔔 تنبيه مبيعات (قاعدة البيانات): العميل ({user_name}) أرسل إيصالاً صحيحاً وتم تسليمه المنتج!")
                else:
                    send_telegram_message(chat_id, "❌ لم نتمكن من التحقق من صحة إيصال التحويل في الصورة. تأكد من وضوحها أو راسل الإدارة.")
            return jsonify({"status": "ok"})

        # الخيارات اليدوية الاحتياطية
        if "تم التحويل للكتاب" in user_text or "Paid Book" in user_text:
            log_sale(chat_id, user_name, "book")
            book_url = "https://raw.githubusercontent.com/Mohammad1991208/my-first-project/main/AI_Guide.pdf"
            send_telegram_document(chat_id, book_url, "شكراً لتأكيد الدفع! تفضل كتاب 'دليل المبتدئ إلى الذكاء الاصطناعي'. 🤖📚")
            if ADMIN_CHAT_ID:
                send_telegram_message(ADMIN_CHAT_ID, f"🔔 تنبيه مبيعات: العميل ({user_name}) طلب الكتاب يدوياً.")
            return jsonify({"status": "ok"})

        if "تم تحويل القوالب" in user_text or "Paid Prompts" in user_text:
            log_sale(chat_id, user_name, "prompts")
            prompts_url = "https://raw.githubusercontent.com/Mohammad1991208/my-first-project/main/Prompts_Guide.txt"
            send_telegram_document(chat_id, prompts_url, "شكراً لتأكيد الدفع! تفضل 'قوالب هندسة الأوامر الاحترافية'. ⚡📝")
            if ADMIN_CHAT_ID:
                send_telegram_message(ADMIN_CHAT_ID, f"🔔 تنبيه مبيعات: العميل ({user_name}) طلب القوالب يدوياً.")
            return jsonify({"status": "ok"})

        # المحادثة الذكية العادية
        reply_text = get_gemini_response(user_text)
        send_telegram_message(chat_id, reply_text, reply_markup=main_keyboard)

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
