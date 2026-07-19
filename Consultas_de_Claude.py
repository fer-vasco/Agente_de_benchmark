import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock
import os
from dotenv import load_dotenv
import requests
import time

# Estos imports son para el registro de los reportes ya generados
import pandas as pd
from pathlib import Path


def Enviar_mensaje(mensaje, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": mensaje}
    response = requests.post(url, data=data)
    
    return response.status_code


async def main(bot_token, chat_id, archivo):

    casos_previos = Leer_casos(archivo)

    mi_prompt= (
        "Buscá en internet un caso sobre mejora logística inbound automotriz."
        "Priorizá casos reales de procesos inbound solamente, de las automtrices más importantes del mundo."
        "Armá un resumen de los logros, las estrategias implementadas, las soluciones eficientes y los problemas resueltos."
        "Explicá lo que hicieron haciendo foco en los puntos fundamentales que permitieron coneguir el logro y mejora."
        "No generes ningún caso complementario."
        "Respondé SOLO con esa línea, sin introducción ni comentarios."
        )

    if casos_previos:
        lista = "\n".join(f"- {c}" for c in casos_previos)
        prompt += (
            "\n\nIMPORTANTE: ya generé reportes sobre los siguientes casos. "
            "NO repitas ninguno de ellos; buscá un caso distinto (otra empresa, "
            "u otro proceso/proyecto si es la misma empresa):\n" + lista
        )


    mensaje = ""
    async for m in query(
        prompt=mi_prompt,
        options=ClaudeAgentOptions(allowed_tools=["WebSearch"]),
    ):
        if isinstance(m, AssistantMessage):
            for b in m.content:
                if isinstance(b, TextBlock):
                    mensaje += b.text + "\n"


    print(mensaje)

    lista_de_submensajes = Dividir_mensaje(mensaje)
    for submensaje in lista_de_submensajes:
        Enviar_mensaje(submensaje, bot_token, chat_id)
        time.sleep(1) # Telegram solo permite 1 mensaje por segundo a un mismo chat

    descripcion = await Registrar_caso(mensaje, archivo)
    print(f"Caso registrado: {descripcion}")




def Dividir_mensaje(mensaje, max_largo=4000):
    # Divide un texto en partes de hasta max_largo caracteres,
    # cortando en saltos de línea o espacios para no partir palabras.
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









async def Generar_descripcion(reporte):
    # Genera una descripción breve del caso a partir del reporte completo.
    prompt = (
        "A continuación te paso un reporte de un caso de mejora logística. "
        "Generá una descripción de UNA sola línea (máximo 30 palabras) que identifique "
        "inequívocamente el caso: empresa, proceso mejorado y logro principal. "
        "Respondé SOLO con esa línea, sin introducción ni comentarios.\n\n"
        f"REPORTE:\n{reporte}"
    )
    descripcion = ""
    async for m in query(prompt=prompt, options=ClaudeAgentOptions(allowed_tools=[])):
        if isinstance(m, AssistantMessage):
            for b in m.content:
                if isinstance(b, TextBlock):
                    descripcion += b.text
    return descripcion.strip()


def Actualizar_casos(descripcion, archivo):
    # Agrega la descripción como nueva fila en la columna 'caso' del csv.
    if Path(archivo).exists():
        df = pd.read_csv(archivo)
    else:
        df = pd.DataFrame(columns=["caso"])
    df = pd.concat([df, pd.DataFrame({"caso": [descripcion]})], ignore_index=True)
    df.to_csv(archivo, index=False)
    return df


async def Registrar_caso(reporte, archivo):
    # Función principal: recibe el reporte, genera la descripción y actualiza el csv.
    descripcion = await Generar_descripcion(reporte)
    Actualizar_casos(descripcion, archivo)
    return descripcion




def Leer_casos(archivo):
    # Devuelve la lista de casos ya reportados (vacía si no existe el archivo).
    if Path(archivo).exists():
        return pd.read_csv(archivo)["caso"].tolist()
    return []



# Inicio del programa
# ===================

load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
ARCHIVO_CASOS = "casos_reportados.csv"
asyncio.run(main(BOT_TOKEN, CHAT_ID, ARCHIVO_CASOS))




# Notas
# Se usan funciones async porque el SDK de Claude Agent es asíncrono, y eso te obliga a usar la sintaxis async:
# 1. query() no devuelve una lista, devuelve un generador asíncrono. El agente no produce toda la respuesta de golpe: mientras corre, va emitiendo mensajes a medida que piensa, busca en la web y escribe. Un generador asíncrono te va "entregando" cada mensaje cuando está disponible, sin bloquear el programa mientras espera la red.
# 2. async for es la única forma de recorrer ese generador. Un for común no sabe "esperar" a que llegue el próximo mensaje por Internet. async for sí: en cada vuelta le dice a Python "pausame acá hasta que el SDK tenga algo nuevo para darme".
# 3. async for solo puede vivir dentro de una función async def. Es una regla del lenguaje: cualquier función que use await o async for debe declararse asíncrona. Por eso main lleva el async.
# 4. asyncio.run(main(...)) es el puente entre ambos mundos. Tu script arranca como código sincrónico normal, y una función async no se ejecuta llamándola directamente (eso solo crea una "corrutina", una promesa de trabajo pendiente). asyncio.run() crea el bucle de eventos de asyncio, ejecuta la corrutina hasta que termina, y cierra todo.