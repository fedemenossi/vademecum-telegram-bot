import os
import pymysql
from pymysql.err import MySQLError
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler

# --- Configuración
TELEGRAM_TOKEN = "TU_TELEGRAM_TOKEN"
CANTIDAD_GRATIS = 5

# --- Config DB
HOST_DB = "centerbeam.proxy.rlwy.net"
PORT_DB = 12935
USER_DB = "root"
PASSWORD_DB = "QbnIpcJeXYYoQYvhnPUjAALwmhmswmmg"
DATABASE_DB = "railway"

def get_db_connection():
    try:
        db = pymysql.connect(
            host=HOST_DB,                                    
            port=PORT_DB,
            user=USER_DB,
            password=PASSWORD_DB,
            database=DATABASE_DB)
        return db
    except MySQLError as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def get_or_create_user(telegram_id, username, nombre, apellido):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE telegram_id = %s", (telegram_id,))
        user = cursor.fetchone()
        if user is None:
            cursor.execute("INSERT INTO usuarios (telegram_id, username, nombre, apellido, consultas) VALUES (%s, %s, %s, %s, 0)",
                           (telegram_id, username, nombre, apellido))
            conn.commit()
        conn.close()

def puede_usar_bot(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT consultas, suscripcion_valida_hasta FROM usuarios WHERE telegram_id = %s", (telegram_id,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return False, "Usuario no registrado"
    consultas, suscripcion_valida_hasta = row
    if suscripcion_valida_hasta:
        sus_valida = datetime.strptime(suscripcion_valida_hasta, "%Y-%m-%d") >= datetime.now()
        if sus_valida:
            return True, "Suscripción activa"
    if consultas < CANTIDAD_GRATIS:
        return True, "Consulta gratuita"
    return False, "Debe pagar"

def registrar_uso(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET consultas = consultas + 1 WHERE telegram_id = %s", (telegram_id,))
    conn.commit()
    conn.close()

def activar_suscripcion(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    nueva_fecha = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    cursor.execute("UPDATE usuarios SET suscripcion_valida_hasta = %s, consultas = 0 WHERE telegram_id = %s",
                   (nueva_fecha, telegram_id))
    conn.commit()
    conn.close()

# --- Handlers de Telegram

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola! Soy un bot con IA. Escribí tu consulta.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Comandos:\n/start - Iniciar\n/help - Ayuda")

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    username = user.username or ""
    nombre = user.first_name or ""
    apellido = user.last_name or ""

    get_or_create_user(telegram_id, username, nombre, apellido)

    permitido, motivo = puede_usar_bot(telegram_id)
    if permitido:
        registrar_uso(telegram_id)
        # Aquí va tu integración con ChatGPT:
        prompt = update.message.text

        # -- INTEGRACIÓN CON CHATGPT (ejemplo usando requests) --
        # response = requests.post("https://api.openai.com/v1/chat/completions", ...)
        # respuesta = response.json()['choices'][0]['message']['content']

        respuesta = "Respuesta de ChatGPT (implementá aquí tu integración)"
        await update.message.reply_text(respuesta)
    else:
        # url_pago = crear_preferencia_pago(telegram_id)
        await update.message.reply_text(
            f"🚫 {motivo}. Por favor, pagá tu suscripción para continuar.")

async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    activar_suscripcion(update.effective_user.id)
    await update.message.reply_text("✅ ¡Gracias por tu pago! Suscripción activada.")

# --- Arrancar el bot
app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
app.add_handler(CommandHandler("pagar", pagar))

print("🤖 Bot iniciado...")
app.run_polling()
