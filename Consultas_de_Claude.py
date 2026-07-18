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
                    Enviar_mensaje(mensaje, bot_token, chat_id)



# Inicio del programa
# ===================

load_dotenv()
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
asyncio.run(main(BOT_TOKEN, CHAT_ID))


