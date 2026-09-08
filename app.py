import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# إعداد السجلات لمتابعة حالة البوت والأخطاء بدقة
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# دالة الاستجابة لأمر البدء /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"أهلاً بك يا {user_name} في عالم الحلول الرقمية الذكية! 🚀\n\n"
        "أنا سارة، مساعدتك الذكية لإدارة المنتجات الرقمية والطلبات."
    )

def main():
    # جلب التوكن بأمان من متغيرات البيئة في المنصة
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("No BOT_TOKEN found in environment variables!")
        return

    # بناء وتشغيل البوت
    application = ApplicationBuilder().token(token).build()
    
    # ربط أمر /start بالدالة
    application.add_handler(CommandHandler("start", start))

    logger.info("Starting Sarah Bot polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
