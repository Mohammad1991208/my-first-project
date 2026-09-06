import os
import asyncio
from flask import Flask, render_template, request, jsonify
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

app = Flask(__name__)

# تعليمات النظام وقاعدة بيانات المبيعات المخصصة لسارة
SYSTEM_INSTRUCTION = """
أنت سارة، وكيلة مبيعات محترفة وودودة لمؤسستنا.
مهامك:
1. الرد على استفسارات العملاء بناءً على الكتالوج والمنتجات والدورات المتاحة.
2. مساعدة العملاء في اختيار المنتج أو الدورة المناسبة.
3. توجيه العميل لرابط الشراء عند رغبته في الطلب.
"""

# إعداد العميل لـ Gemini API
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

# إعداد تطبيق تلجرام
telegram_token = os.environ.get("TELEGRAM_TOKEN")
tg_app = None

if telegram_token:
    tg_app = ApplicationBuilder().token(telegram_token).build()

async def start_command(update, context):
    await update.message.reply_text("أهلاً بك! أنا سارة، كيف يمكنني مساعدتك اليوم؟ 😊")

async def handle_message(update, context):
    user_text = update.message.text
    try:
        if not client:
            await update.message.reply_text("عذراً، مفتاح GEMINI_API_KEY غير متهيئة بشكل صحيح.")
            return

        # استدعى النموذج الصحيح gemini-1.5-flash
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=user_text,
            config={"system_instruction": SYSTEM_INSTRUCTION}
        )
        reply_text = response.text if response.text else "عذراً، لم أتمكن من معالجة الطلب."
        await update.message.reply_text(reply_text)
    except Exception as e:
        print(f"Error in handle_message: {e}")
        await update.message.reply_text("عذراً، حدث خطأ مؤقت. يرجى المحاولة لاحقاً.")

# إضافة معالجات الأوامر والرسائل
if tg_app:
    tg_app.add_handler(CommandHandler("start", start_command))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route("/", methods=["GET"])
def index():
    return "Sarah Sales Agent is running!"

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    if not tg_app:
        return jsonify({"status": "error", "message": "Telegram app not configured"}), 500
    
    update_data = request.get_json(force=True)
    update = Update.de_json(update_data, tg_app.bot)
    
    # تشغيل معالجة التلجرام بشكل غير متزامن
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(tg_app.process_update(update))
    loop.close()
    
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
