import os
import pymysql
from pymysql.err import MySQLError
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from openai import OpenAI
from dotenv import load_dotenv
import threading
# Mercado Pago SDK
import mercadopago
#Flask para manejar pagos
import threading
from flask import Flask, request, jsonify
import asyncio

# Cargar variables de entorno desde un archivo .env
load_dotenv()
# --- Config DB
# Configuración de la base de datos
# Asegúrate de que estas variables estén definidas en tu archivo .env
HOST_DB = os.getenv("HOST_DB")
PORT_DB = int(os.getenv("PORT_DB", 3306))
USER_DB = os.getenv("USER_DB")
PASSWORD_DB = os.getenv("PASSWORD_DB")
DATABASE_DB = os.getenv("DATABASE_DB")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

## --- Configuración cantidad de consultas gratis
CANTIDAD_GRATIS = 5

# Configurar tu API key de OpenAI desde una variable de entorno
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
URL_MP = os.getenv("URL_MP")
# --- Funciones de ChatGPT


def get_db_connection():
    try:
        return pymysql.connect(
            host=HOST_DB,
            port=PORT_DB,
            user=USER_DB,
            password=PASSWORD_DB,
            database=DATABASE_DB
        )
    except MySQLError as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def get_or_create_user(telegram_id, username, nombre, apellido):
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM usuarios WHERE telegram_id = %s", (telegram_id,))
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO usuarios (telegram_id, username, nombre, apellido, consultas) VALUES (%s, %s, %s, %s, 0)",
                    (telegram_id, username, nombre, apellido)
                )
                conn.commit()
    except MySQLError as e:
        print(f"Error en get_or_create_user: {e}")
    finally:
        conn.close()
        
def crear_preferencia_pago(telegram_id):
    if not MP_ACCESS_TOKEN:
        print("No hay access token de Mercado Pago configurado.")
        return None
    try:
        mp = mercadopago.SDK(MP_ACCESS_TOKEN)
        preference_data = {
            "items": [
                {
                    "title": "Suscripción Vademécum Bot",
                    "quantity": 1,
                    "unit_price": 1000.00  # Cambia el precio si lo necesitás
                }
            ],
            "metadata": {
                "telegram_id": str(telegram_id)
            },
            "back_urls": {
                "success": "hhttps://t.me/medicoenlinea_bot",  # Cambia por tu bot real si querés
                "failure": "https://prueba-production-a391.up.railway.app/",
                "pending": "https://prueba-production-a391.up.railway.app/"
            },
            "auto_return": "approved"
        }
        preference_response = mp.preference().create(preference_data)
        return preference_response["response"]["init_point"]
    except Exception as e:
        print(f"Error creando preferencia de pago: {e}")
        return None


def puede_usar_bot(telegram_id):
    conn = get_db_connection()
    if not conn:
        return False, "Error de base de datos"
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT consultas, suscripcion_valida_hasta FROM usuarios WHERE telegram_id = %s", (telegram_id,))
            row = cursor.fetchone()
    except MySQLError as e:
        print(f"Error ejecutando consulta: {e}")
        return False, "Error de base de datos"
    finally:
        conn.close()

    # Si el usuario no existe, permitir la consulta (se creará en get_or_create_user)
    if not row:
        return True, "Consulta gratuita"
    consultas, suscripcion_valida_hasta = row
    if suscripcion_valida_hasta:
        try:
            sus_valida = datetime.strptime(str(suscripcion_valida_hasta), "%Y-%m-%d") >= datetime.now()
        except Exception:
            sus_valida = False
        if sus_valida:
            return True, "Suscripción activa"
    if consultas < CANTIDAD_GRATIS:
        return True, "Consulta gratuita"
    return False, "Debe pagar"

def registrar_uso(telegram_id):
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE usuarios SET consultas = consultas + 1 WHERE telegram_id = %s", (telegram_id,))
            conn.commit()
    except MySQLError as e:
        print(f"Error en registrar_uso: {e}")
    finally:
        conn.close()

def activar_suscripcion(telegram_id):
    conn = get_db_connection()
    if not conn:
        return
    try:
        nueva_fecha = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE usuarios SET suscripcion_valida_hasta = %s, consultas = 0 WHERE telegram_id = %s",
                (nueva_fecha, telegram_id)
            )
            conn.commit()
    except MySQLError as e:
        print(f"Error en activar_suscripcion: {e}")
    finally:
        conn.close()

# --- Funciones de ChatGPT
def preguntar_a_chatgpt(mensaje_usuario):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sos un asistente amable y experto."},
                {"role": "user", "content": mensaje_usuario}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error consultando a ChatGPT: {e}")
        return "⚠️ Error consultando a ChatGPT. Intenta nuevamente."

# --- Handlers de Telegram

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola! Soy tu medico en linea, puedes consultarme lo que quieras.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Comandos:\n/start - Iniciar\n/help - Ayuda")

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id
    username = user.username or ""
    nombre = user.first_name or ""
    apellido = user.last_name or ""

    # Si no existe el usuario, lo crea
    get_or_create_user(telegram_id, username, nombre, apellido)
    permitido, motivo = puede_usar_bot(telegram_id)
    if permitido:
        registrar_uso(telegram_id)
        pregunta = update.message.text
        respuesta_ia = preguntar_a_chatgpt(pregunta)
        await update.message.reply_text(respuesta_ia)
    else:
        link_pago = crear_preferencia_pago(telegram_id)
        if link_pago:
            await update.message.reply_text(
                f"🚫 {motivo}. Para continuar, pagá tu suscripción aquí:\n{link_pago}"
            )
        else:
            await update.message.reply_text(
                f"🚫 {motivo}. No se pudo generar el link de pago. Contacta soporte."
            )


# El comando /pagar solo informa el link de pago
async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    link_pago = crear_preferencia_pago(telegram_id)
    if link_pago:
        await update.message.reply_text(f"Para pagar tu suscripción, hacé click aquí:\n{link_pago}")
    else:
        await update.message.reply_text("No se pudo generar el link de pago. Contacta soporte.")


# ---- Flask Webhook para Mercado Pago ----
flask_app = Flask(__name__)

@flask_app.route("/", methods=["GET"])
def index():
    return "OK! Flask está corriendo 🚀"

@flask_app.route("/webhook_mercadopago", methods=["GET"])
def webhook_mercadopago_get():
    return "Webhook activo para Mercado Pago", 200

@flask_app.route("/webhook_mercadopago", methods=["POST"])
def webhook_mercadopago():
    # Soporta tanto POST (con JSON) como GET (con query string)
    payment_id = None
    topic = None
    if request.method == "POST":
        data = request.get_json() or {}
        print("Recibí webhook POST:", data)
        # Intentar obtener payment_id y topic desde el body
        topic = data.get('topic') or data.get('type')
        if 'data' in data and isinstance(data['data'], dict):
            payment_id = data['data'].get('id')
        # Si no viene en el body, buscar en query string
        if not payment_id:
            payment_id = request.args.get('id')
        if not topic:
            topic = request.args.get('topic')
    else:
        # GET: Mercado Pago puede enviar topic e id por query string
        payment_id = request.args.get('id')
        topic = request.args.get('topic')
        print(f"Recibí webhook GET: topic={topic}, id={payment_id}")

    if topic == 'payment' and payment_id:
        import mercadopago
        mp = mercadopago.SDK(MP_ACCESS_TOKEN)
        payment = mp.payment().get(payment_id)
        info = payment['response']
        print("Detalles del pago:", info)

        if info.get('status') == 'approved':
            telegram_id = info.get('metadata', {}).get('telegram_id')
            if telegram_id:
                activar_suscripcion(telegram_id)
                print(f"Suscripción activada para {telegram_id}")
        return jsonify({"status": "ok"})
    return jsonify({"status": "ignored"})

@flask_app.route("/webhook_mercadopago", methods=["GET"])
def webhook_mercadopago_get():
    return "Webhook de Mercado Pago activo", 200    


def run_telegram():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.run_polling(stop_signals=[])


# --- Arrancar el bot
app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
app.add_handler(CommandHandler("pagar", pagar))

if __name__ == "__main__":
    # Bot en thread aparte, creando event loop
    bot_thread = threading.Thread(target=run_telegram)
    bot_thread.start()
    # Flask en el main thread (necesario para Railway)
    #port = int(os.environ.get("PORT", 8000))
    #print(f"🌐 Flask escuchando en el puerto {port}")
    #port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0")
