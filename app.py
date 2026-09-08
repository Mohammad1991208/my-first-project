import os
import logging
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# إعداد السجلات لمتابعة حالة البوت والأخطاء بدقة
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# إنشاء تطبيق ويب خفيف لإرضاء متطلبات البورت في منصة Railway
app = Flask(__name__)

@app.route('/')
def home():
    return "Sarah Bot is active and running successfully!"

# دالة الاستجابة لأمر البدء /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"أهلاً بك يا {user_name} في عالم الحلول الرقمية الذكية! 🚀\n\n"
        "أنا سارة، مساعدتك الذكية لإدارة المنتجات الرقمية والطلبات."
    )

def main():
    # قراءة التوكن بأمان من متغيرات البيئة في المنصة
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("No BOT_TOKEN found in environment variables!")
        return

    # بناء وتشغيل تطبيق تيليجرام
    application = ApplicationBuilder().token(token).build()

    # ربط أمر /start بالدالة الخاصة به
    application.add_handler(CommandHandler("start", start))

    # جلب رقم المنفذ (Port) المخصص من Railway أو استخدام 5000 محلياً
    port = int(os.environ.get("PORT", 5000))

    logger.info("Starting bot and web server...")

    # تشغيل خادم الويب على البورت الخاص بـ Railway في الخلفية إذا لزم الأمر، 
    # أو الاعتماد على تفعيل Polling المباشر مع ضبط أمر التشغيل (Start Command).
    # ملاحظة: إذا كان خادم الويب يمنع عمل البوت، يمكنك تشغيل Flask عبر مكتبة threading لتشغيلهما معاً.
    
    application.run_polling()

if __name__ == '__main__':
    main()
