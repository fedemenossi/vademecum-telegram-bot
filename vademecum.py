import os
import pymysql
from pymysql.err import MySQLError
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from openai import OpenAI
from dotenv import load_dotenv

# --- Configuración cantiedad de consultas gratis
CANTIDAD_GRATIS = 5

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Configurar tu API key de OpenAI desde una variable de entorno
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Config DB
# Configuración de la base de datos
# Asegúrate de que estas variables estén definidas en tu archivo .env
HOST_DB = os.getenv("HOST_DB")
PORT_DB = int(os.getenv("PORT_DB", 3306))
USER_DB = os.getenv("USER_DB")
PASSWORD_DB = os.getenv("PASSWORD_DB")
DATABASE_DB = os.getenv("DATABASE_DB")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

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
    row = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT consultas, suscripcion_valida_hasta FROM usuarios WHERE telegram_id = %s", (telegram_id,))
        row = cursor.fetchone()
    except MySQLError as e:
        print(f"Error ejecutando consulta: {e}")
        return False, "Error de base de datos"
    finally:
        if conn:
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


# --- Funciones de ChatGPT
def preguntar_a_chatgpt(mensaje_usuario):
    try:
        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sos un asistente amable y experto."},
                {"role": "user", "content": mensaje_usuario}
            ],
            max_tokens=800,
            temperature=0.7
        )
        if not respuesta.choices:
            return "No se recibió respuesta de ChatGPT."
        return respuesta.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error consultando a ChatGPT: {e}"



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
        pregunta = update.message.text
        respuesta_ia = preguntar_a_chatgpt(pregunta)
        await update.message.reply_text(respuesta_ia)
        
        #prompt = update.message.text

        # -- INTEGRACIÓN CON CHATGPT (ejemplo usando requests) --
        # response = requests.post("https://api.openai.com/v1/chat/completions", ...)
        # respuesta = response.json()['choices'][0]['message']['content']

        #respuesta = "Respuesta de ChatGPT (implementá aquí tu integración)"
        #await update.message.reply_text(respuesta)
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
