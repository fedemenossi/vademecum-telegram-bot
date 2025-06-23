import os
import logging
import requests
import json
import mercadopago
import pymysql
from pymysql.err import MySQLError
#from deep_translator import GoogleTranslator
from datetime import datetime  # <-- Esta línea soluciona tu error
from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler 
import requests
import xml.etree.ElementTree as ET
import re
import html
from datetime import datetime, timedelta

#sdk = mercadopago.SDK("TU_ACCESS_TOKEN")

CANTIDAD_GRATIS = 5

TELEGRAM_TOKEN = "7976779147:AAGi_06PH9rlRho2rm5MMV7BT9n84xN6Ww4"
OPENWEATHER_API_KEY = "1fcd18ec464cb20595a106f0bc1eb3c4"
MAX_LEN = 4000  # un poco menos que el límite para dejar margen

## Variables de base de datos
# Conexión a la base de datos MySQL

HOST_DB="centerbeam.proxy.rlwy.net"
PORT_DB=12935
USER_DB="root"
PASSWORD_DB="QbnIpcJeXYYoQYvhnPUjAALwmhmswmmg"
#PASSWORD_DB = os.environ.get("MYSQL_PASSWORD")
DATABASE_DB="railway"


def get_db_connection():
    try:
        db = pymysql.connect(
        host=HOST_DB,                                    
        port=PORT_DB,
        user=USER_DB,
        password=PASSWORD_DB,
        database=DATABASE_DB)
        print("Conexión exitosa a la base de datos MySQL")
        return db
    except MySQLError  as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None


# 🧠 Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola! Preguntame el clima para mañana en una ciudad. Ej: 'clima en Mendoza mañana'. Esto es una prueba.")
    
# 🧠 Comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
     await update.message.reply_text("🛠 Comandos:\n/start - Iniciar\n/help - Ayuda")


# 🧠 creacion de usuarios
def get_or_create_user(telegram_id, username, nombre, apellido):
    conn = get_db_connection()
    if conn:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE telegram_id = %s", (telegram_id,))
        user = cursor.fetchone()

        if user is None:
            #cursor.execute("INSERT INTO usuarios (telegram_id, username, nombre, apellido, consultas, suscripcion_valida_hasta) VALUES (?, ?, ?, ?, 0, NULL)",
            #           (telegram_id, username, nombre, apellido))
            
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

# Activar suscripción manualmente (ejemplo)
def activar_suscripcion(telegram_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    nueva_fecha = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    cursor.execute("UPDATE usuarios SET suscripcion_valida_hasta = %s, consultas = 0 WHERE telegram_id = %s",
                   (nueva_fecha, telegram_id))
    conn.commit()
    conn.close()
    
    
def crear_preferencia_pago(telegram_id):
    
    preference_data = {
        "items": [
            {
                "title": "Suscripción Bot Telegram - 30 días",
                "quantity": 1,
                "unit_price": 1000.0
            }
        ],
        "payer": {
            "telegram_id": telegram_id
        },
        "notification_url": "https://tu-servidor.com/webhook",  # Webhook donde te avisa Mercado Pago
        "auto_return": "approved",
        "back_urls": {
            "success": "https://tubot.com/gracias",
            "failure": "https://tubot.com/error",
            "pending": "https://tubot.com/esperando"
        }
    }

    preference_response = sdk.preference().create(preference_data)
    return preference_response["response"]["init_point"]

# Manejador de mensajes
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
        await update.message.reply_text(f"✅ Consulta recibida. Motivo: {motivo}")
        # Acá va la lógica del bot real.
    else:
        #url=crear_preferencia_pago(telegram_id)
        url="https://www.google.com"
        await update.message.reply_text(f"🚫 {motivo}. Por favor, pagá tu suscripción para continuar.\n\n[💳 Pagar ahora]({url})", parse_mode='Markdown')
        #await update.message.reply_text(f"🚫 {motivo}. Por favor, pagá tu suscripción para continuar.\n\n[💳 Pagar ahora](https://tu-link-de-pago.com)", parse_mode='Markdown')



def traducir_a_espanol(texto):
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "auto",  # idioma de origen
            "tl": "es",    # traducir a español
            "dt": "t",
            "q": texto,
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            resultado = response.json()
            texto_traducido = ''.join([parte[0] for parte in resultado[0]])
            return texto_traducido
        else:
            return f"[Error {response.status_code} al traducir]"
    except Exception as e:
        return f"[Error al traducir: {e}]"

def limpiar_html(texto):
    # Decodifica entidades HTML
    texto = html.unescape(texto)
    # Elimina etiquetas HTML o XML
    texto = re.sub(r'<[^>]+>', '', texto)
    # Elimina saltos de línea múltiples y espacios extra
    texto = re.sub(r'\n+', '\n', texto).strip()
    return texto

def truncar_mensaje(texto):
    if len(texto) > MAX_LEN:
        return texto[:MAX_LEN] + "\n\n[Mensaje truncado por exceso de longitud]"
    return texto

def dividir_mensaje(texto, max_len=4000):
    partes = []
    while len(texto) > max_len:
        # Buscar último salto de línea antes de max_len para no cortar palabras
        corte = texto.rfind('\n', 0, max_len)
        if corte == -1:
            corte = max_len
        partes.append(texto[:corte])
        texto = texto[corte:].lstrip('\n')
    partes.append(texto)
    return partes

def buscar_medlineplus(termino):
    base_url = "https://wsearch.nlm.nih.gov/ws/query"
    params = {
        "db": "healthTopics",
        "term": termino,
        "lang": "es"
    }

    response = requests.get(base_url, params=params)
    
    if response.status_code != 200:
        return f"Error al hacer la solicitud: {response.status_code}"

    root = ET.fromstring(response.text)

    documentos = root.findall(".//document")
    
    if not documentos:
        return "No se encontró información sobre ese término...."

    resultados = []

    for doc in documentos:
        titulo = None
        resumen = None
        url = doc.get("url") or doc.attrib.get("url")
        
        for content in doc.findall("content"):
            if content.attrib.get("name") == "title" and titulo is None:
                titulo = traducir_a_espanol(limpiar_html("".join(content.itertext()).strip()))
            elif content.attrib.get("name") == "FullSummary" and resumen is None:
                resumen = traducir_a_espanol(limpiar_html("".join(content.itertext()).strip()))

        if titulo and resumen and url:
            resultados.append(f"Título: {titulo}\nResumen: {resumen}\nURL: {url}\n")

    if resultados:
        return "\n---\n".join(resultados[:2])  # Devuelve los primeros 2 resultados
    else:
        return "Se encontraron documentos, pero no contenían resumen o título válido."


async def pagar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    activar_suscripcion(update.effective_user.id)
    await update.message.reply_text("✅ ¡Gracias por tu pago! Tu suscripción ha sido activada por 30 días.")

    
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    termino = update.message.text
    resultado = buscar_medlineplus(termino)
    partes = dividir_mensaje(resultado)
    for parte in partes:
        await update.message.reply_markdown(parte)
    
# ⚙️ Bot
app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
#app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
#app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
#app.add_handler(CallbackQueryHandler(boton_presionado))
app.add_handler(CommandHandler("pagar", pagar))  # Solo para pruebas


print("🌦 Bot de Vademecum iniciado...")
app.run_polling()
