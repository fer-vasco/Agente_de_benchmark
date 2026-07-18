import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock
import os
from dotenv import load_dotenv
import requests


def Enviar_mensaje(mensaje, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": mensaje}
    response = requests.post(url, data=data)
    
    return response.status_code


async def main(bot_token, chat_id):
    async for m in query(
        prompt="Buscá en internet un caso sobre mejora logística inbound automotriz. Prioricá casos reales de procesos inbound solamente, de las automtrices más importantes del mundo. Armá un resumen de los logros, las estrategias implementadas, las soluciones eficientes y los problemas resueltos. Explicá lo que hicieron haciendo foco en los puntos fundamentales que permitieron coneguir el logro y mejora.",
        options=ClaudeAgentOptions(allowed_tools=["WebSearch"]),
    ):
        if isinstance(m, AssistantMessage):
            for b in m.content:
                if isinstance(b, TextBlock):
                    mensaje = b.text
                    print(mensaje)

                    lista_de_submensajes = Dividir_mensaje(mensaje)
                    for submensaje in lista_de_submensajes:
                        Enviar_mensaje(submensaje, bot_token, chat_id)



def Dividir_mensaje(mensaje, max_largo=4000):
    """Divide un texto en partes de hasta max_largo caracteres,
    cortando en saltos de línea o espacios para no partir palabras."""
    partes = []
    while mensaje:
        if len(mensaje) <= max_largo:
            partes.append(mensaje)
            break
        corte = mensaje.rfind("\n", 0, max_largo)
        if corte == -1:
            corte = mensaje.rfind(" ", 0, max_largo)
        if corte == -1:
            corte = max_largo
        partes.append(mensaje[:corte])
        mensaje = mensaje[corte:].lstrip()
    return partes




# Inicio del programa
# ===================

load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
asyncio.run(main(BOT_TOKEN, CHAT_ID))




# Notas
# Se usan funciones async porque el SDK de Claude Agent es asíncrono, y eso te obliga a usar la sintaxis async:
# 1. query() no devuelve una lista, devuelve un generador asíncrono. El agente no produce toda la respuesta de golpe: mientras corre, va emitiendo mensajes a medida que piensa, busca en la web y escribe. Un generador asíncrono te va "entregando" cada mensaje cuando está disponible, sin bloquear el programa mientras espera la red.
# 2. async for es la única forma de recorrer ese generador. Un for común no sabe "esperar" a que llegue el próximo mensaje por Internet. async for sí: en cada vuelta le dice a Python "pausame acá hasta que el SDK tenga algo nuevo para darme".
# 3. async for solo puede vivir dentro de una función async def. Es una regla del lenguaje: cualquier función que use await o async for debe declararse asíncrona. Por eso main lleva el async.
# 4. asyncio.run(main(...)) es el puente entre ambos mundos. Tu script arranca como código sincrónico normal, y una función async no se ejecuta llamándola directamente (eso solo crea una "corrutina", una promesa de trabajo pendiente). asyncio.run() crea el bucle de eventos de asyncio, ejecuta la corrutina hasta que termina, y cierra todo.