import logging
import requests
import json
#from deep_translator import GoogleTranslator
from datetime import datetime  # <-- Esta línea soluciona tu error
from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler 
import requests
import xml.etree.ElementTree as ET
import re
import html


#translator = Translator()


TELEGRAM_TOKEN = "7976779147:AAGi_06PH9rlRho2rm5MMV7BT9n84xN6Ww4"
OPENWEATHER_API_KEY = "1fcd18ec464cb20595a106f0bc1eb3c4"

# 🧠 Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola! Preguntame el clima para mañana en una ciudad. Ej: 'clima en Mendoza mañana'.")
    
# 🧠 Comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
     await update.message.reply_text("🛠 Comandos:\n/start - Iniciar\n/help - Ayuda")

MAX_LEN = 4000  # un poco menos que el límite para dejar margen

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
        return "No se encontró información sobre ese término."

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


#print(buscar_medlineplus("diabetes"))
#async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
#    termino = update.message.text
#    resultado = buscar_medlineplus(termino)
#    await update.message.reply_markdown(resultado)
    
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
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
#app.add_handler(CallbackQueryHandler(boton_presionado))

print("🌦 Bot de Vademecum iniciado...")
app.run_polling()
