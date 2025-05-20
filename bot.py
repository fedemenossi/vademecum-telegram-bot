
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! Soy tu bot en Telegram usando PTB 22.1")

# Comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛠 Comandos:\n/start - Iniciar\n/help - Ayuda")

# Función principal
async def main():
    # Reemplazá con tu token real de BotFather
    TOKEN = "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ"

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    print("🤖 Bot iniciado con PTB 22.1")
    await app.run_polling()

# Iniciar
if __name__ == "__main__":
    asyncio.run(main())
    
    
    
