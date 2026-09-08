import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# إعداد السجلات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء خادم ويب مصغر لرضا منصة Railway فقط
app = Flask(__name__)

@app.route('/')
def home():
    return "Sarah Bot is active and running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# دالة البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"أهلاً بك يا {user_name} في عالم الحلول الرقمية الذكية! 🚀\n\n"
        "أنا سارة، مساعدتك الذكية لإدارة المنتجات الرقمية والطلبات."
    )

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("No BOT_TOKEN found in environment variables!")
        return

    # تشغيل خادم الويب في خلفية منفصلة لكي لا يتعارض مع البوت
    web_thread = Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    # تشغيل بوت تيليجرام الأساسي
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))

    logger.info("Starting Sarah Bot polling with embedded web server...")
    application.run_polling()

if __name__ == '__main__':
    main()
