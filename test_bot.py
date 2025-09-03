import logging
from telegram.ext import Updater, CommandHandler

logging.basicConfig(level=logging.INFO)
BOT_TOKEN = "8246985665:AAGpHgRVwU3t8vHGwE1bfRxrGGgeJWwyAKA"

def start(bot, update):
    update.message.reply_text("✅ Бот работает с вашим токеном!")

updater = Updater(BOT_TOKEN)
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.start_polling()
updater.idle()