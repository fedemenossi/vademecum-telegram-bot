from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! Soy tu bot de Telegram. Hola Lau como andas ? ")

if __name__ == "__main__":
    TOKEN = "7976779147:AAGi_06PH9rlRho2rm5MMV7BT9n84xN6Ww4"

    # Crear la aplicación del bot
    app = Application.builder().token(TOKEN).build()

    # Agregar el manejador para el comando /start
    app.add_handler(CommandHandler("start", start))

    print("🤖 Bot iniciado correctamente.")
    app.run_polling()
