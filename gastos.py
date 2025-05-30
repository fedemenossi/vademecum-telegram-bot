import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Autenticación
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
client = gspread.authorize(creds)

# Abrir la hoja
spreadsheet = client.open("Copia de Finanzas e Ingresos y egresos 2025")  # El nombre de tu hoja
worksheet = spreadsheet.sheet1  # Primera pestaña

# Escribir datos: ejemplo ingreso nuevo
worksheet.append_row(["2025-05-29", "Ingreso", "Sueldo", 250000])