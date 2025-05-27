import logging
import requests
import json
from datetime import datetime  # <-- Esta línea soluciona tu error
from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler, CallbackQueryHandler 
import requests
import xml.etree.ElementTree as ET



# 🔐 Tokens

TELEGRAM_TOKEN = "7976779147:AAGi_06PH9rlRho2rm5MMV7BT9n84xN6Ww4"
OPENWEATHER_API_KEY = "1fcd18ec464cb20595a106f0bc1eb3c4"

# 📢 Logs
logging.basicConfig(level=logging.INFO)

# Función para consultar MedlinePlus
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
                titulo = "".join(content.itertext()).strip()
            elif content.attrib.get("name") == "FullSummary" and resumen is None:
                resumen = "".join(content.itertext()).strip()

        if titulo and resumen and url:
            resultados.append(f"Título: {titulo}\nResumen: {resumen}\nURL: {url}\n")

    if resultados:
        return "\n---\n".join(resultados[:2])  # Devuelve los primeros 2 resultados
    else:
        return "Se encontraron documentos, pero no contenían resumen o título válido."

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    termino = update.message.text
    resultado = buscar_medlineplus(termino)
    await update.message.reply_markdown(resultado)
    


# 🧠 Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola! Preguntame el clima para mañana en una ciudad. Ej: 'clima en Mendoza mañana'.")
    
# 🧠 Comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
     await update.message.reply_text("🛠 Comandos:\n/start - Iniciar\n/help - Ayuda")


# 🌦 Función para obtener el clima
def obtener_clima_maniana(ciudad):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={ciudad}&appid={OPENWEATHER_API_KEY}&units=metric&lang=es"
    ##url = f"http://api.openweathermap.org/data/2.5/forecast?q=buenos%20aires&appid=5d706dee4aca781a6468b860e604bf45&units=metric&lang=es"
    res = requests.get(url)
    if res.status_code != 200:
        return None
     
    data = res.json()
    # Buscar la previsión para mañana al mediodía
        
    
    for entrada in data["list"]:
        dt = datetime.fromtimestamp(entrada['dt'])  # Convertir timestamp a fecha
        temp = entrada['main']['temp']
        desc = entrada['weather'][0]['description']
        
        ##returnf"{dt.strftime('%Y-%m-%d %H:%M:%S')} - Temp: {temp}°C - Clima: {desc}"
        
        
        if "12:00:00" in entrada["dt_txt"]:
            descripcion = entrada["weather"][0]["description"]
            temp = entrada["main"]["temp"]
            temp_feel = entrada["main"]["feels_like"]
            
            return f"Temp Actual: {temp} °C - Sensacion Terminca: {temp_feel} -  Clima: {desc}"
    return "No encontré el pronóstico para mañana."


# 🤖 Manejo de mensajes
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower()
    ciudad=texto
    respuesta=obtener_clima_maniana(ciudad)
    
    if respuesta:
        await update.message.reply_text(respuesta)
    else:
        await update.message.reply_text("No pude obtener el clima. Asegurate de escribir bien la ciudad.")    
  
   



async def boton_presionado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Esto le avisa a Telegram que respondimos el botón (evita el ícono de carga)

    if query.data == 'buenos aires':
        await query.edit_message_text("Consultando el clima de Buenos Aires...")
        respuesta = obtener_clima_maniana(query.data)
        await query.message.reply_text(respuesta)
        # Podés hacer una llamada a tu función de clima acá

    elif query.data == 'paris':
        await query.edit_message_text("Consultando el clima de Paris...")
        respuesta = obtener_clima_maniana(query.data)
        await query.message.reply_text(respuesta)

    elif query.data == 'londres':
        await query.edit_message_text("Consultando el clima de Londres...")
        respuesta = obtener_clima_maniana(query.data)
        await query.message.reply_text(respuesta)
        #await query.edit_message_text("Tomas que te importa el clima en Londres si no estas ahí!!!")
        



# ⚙️ Bot
app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
#app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
#app.add_handler(CallbackQueryHandler(boton_presionado))

print("🌦 Bot de Vademecum iniciado...")
app.run_polling()
