import os
from openai import OpenAI

# Configurar tu API key directamente o usando variables de entorno
client = OpenAI(
    api_key="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"
)

def responder_ia(pregunta):
    respuesta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Sos un asistente útil."},
            {"role": "user", "content": pregunta}
        ]
    )
    return respuesta.choices[0].message.content.strip()

# Bucle interactivo
print("Escribí tu pregunta ('salir' para terminar):")
while True:
    entrada = input("Yo: ")
    if entrada.lower() == "salir":
        print("👋 ¡Hasta luego!")
        break
    respuesta = responder_ia(entrada)
    print("🤖 Bot:", respuesta)
