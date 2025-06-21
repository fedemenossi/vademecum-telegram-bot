from flask import Flask, request
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data and 'type' in data and data['type'] == 'payment':
        payment_id = data['data']['id']
        print(f"Pago recibido, ID: {payment_id}")
        # Procesar el pago
        verificar_pago_y_activar_usuario(payment_id)
    return "OK", 200

def verificar_pago_y_activar_usuario(payment_id):
    import mercadopago
    sdk = mercadopago.SDK("TU_ACCESS_TOKEN")

    result = sdk.payment().get(payment_id)
    payment = result["response"]

    if payment["status"] == "approved":
        email = payment["payer"]["email"]
        print(f"✅ Pago aprobado de {email}")
        activar_usuario_por_email(email)

def activar_usuario_por_email(email):
    conn = sqlite3.connect("usuarios.db")
    cursor = conn.cursor()
    nueva_fecha = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    cursor.execute("UPDATE usuarios SET suscripcion_valida_hasta = ?, consultas = 0 WHERE username = ?", (nueva_fecha, email))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    app.run(port=5000)
