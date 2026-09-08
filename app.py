import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"أهلاً بك يا {user_name}! 🚀\nأنا سارة، مساعدتك الذكية لإدارة المنتجات الرقمية."
    )

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("No BOT_TOKEN found!")
        return

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))

    logger.info("Starting Sarah Bot polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
