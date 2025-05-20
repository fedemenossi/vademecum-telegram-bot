import openai
from openai import OpenAI

client = OpenAI(api_key="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")

def responder_ia(pregunta):
    respuesta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Sos un asistente útil."},
            {"role": "user", "content": pregunta}
        ]
    )
    return respuesta.choices[0].message.content.strip()


# Bucle de conversación
##while True:
##    entrada = input("Vos: ")
##    if entrada.lower() in ["salir", "exit", "bye"]:
##        print("Bot: ¡Hasta la próxima!")
##        break
##    respuesta = responder_ia(entrada)
##    print("Bot:", respuesta)
    
    # Bucle interactivo
print("Escribí tu pregunta ('salir' para terminar):")
while True:
    entrada = input("Yo: ")
    if entrada.lower() == "salir":
        print("👋 ¡Hasta luego!")
        break
    respuesta = responder_ia(entrada)
    print("🤖 Bot:", respuesta)