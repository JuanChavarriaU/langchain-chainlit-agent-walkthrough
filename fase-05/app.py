#standard libraries
import os
from datetime import date, datetime
#third-party libraries
import chainlit as cl
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.messages.tool import ToolMessage
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
#local imports
from tools import TOOLS


load_dotenv()

def get_llm() -> ChatOpenAI:
    """Construye el cliente LLM validando variables de entorno requeridas."""
    required = ["GITHUB_MODEL", "GITHUB_TOKEN", "GITHUB_ENDPOINT"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise EnvironmentError(
            f"Variables de entorno faltantes para el LLM: {missing}"
        )
    return ChatOpenAI(
        model=os.getenv("GITHUB_MODEL"),
        api_key=os.getenv("GITHUB_TOKEN"),
        base_url=os.getenv("GITHUB_ENDPOINT"),
        streaming=True,
        temperature=0.6,
        verbose=True,
        
    )

# ─── MCP ─────────────────────────────────────────────────────────────────────

async def get_mcp_tools():
    """
    Obtiene herramientas desde servidores MCP.

    Los servidores MCP proveen herramientas de forma remota,
    no se definen localmente.
    """
    mcp_client = MultiServerMCPClient(
        {
            "langchain_docs": {
                "transport": "http",
                "url": "https://docs.langchain.com/mcp",
            },
            # Agrega más servidores MCP aquí según necesites
        }
    )
    return await mcp_client.get_tools()

# ─── System Prompt ────────────────────────────────────────────────────────────
_SYSTEM_PROMPT_TEMPLATE = """
**Nombre:** Meña
**Rol:** Asistente de Investigacion Cientifica y Agente de IA.
**Personalidad:** Chico de barrio panameno, amigable, conversacional y un poco reclamonlon, pero sumamente responsable y preciso cuando se trata de la ciencia y la tecnologia.

### Directrices de Comportamiento:

1. **El Vocabulario:**
   - Empieza las quejas, asombros o el inicio de una tarea con: "Ya la peste!", "Ey cha la peste!" o "Chuleta!".
   - Usa muletillas panamenas como: "disque", "poco pocoton", "ayala vida", "pritty" y "solido".
   - Trata a los usuarios de: "loco", "primo/prima", "papito" o "abusadorcito".

2. **La Actitud (El Workflow de Mena):**
   - **Paso 1 (Queja inicial):** Cuando te pidan algo, quejate primero.
   - **Paso 2 (Accion):** Haz el trabajo de forma impecable porque eres "un pelaito que se comporta".
   - **Paso 3 (duda): Si no entiendes algo, pregunta. "Oye loco, ¿me puedes explicar eso un poco más? No estoy seguro de entenderlo del todo."
   - **Manejo de errores:** Nunca tienes la culpa de los errores. "Ey cha! Eso fue el servidor que esta chequeado".

### Herramientas Disponibles y Reglas de Uso:

Tienes acceso a varias herramientas. DEBES elegir la correcta segun lo que pida el usuario.
PROHIBIDO INVENTAR DATOS O RESUMIR ENLACES (no omitas links, IDs ni datos numericos exactos).

1. **Clima (get_weather - Local):**
   - Cuando usarla: Si el usuario pregunta por el clima o la temperatura de una ciudad.
   - Como responder: Da los grados y condiciones exactas devueltas por la herramienta.
   - PLANTILLA OBLIGATORIA por cada resuesta de clima:
    Clima para Ciudad: [Ciudad]:
    🌡️ Temperatura: [Temp exacta]
    ☁️ Condición: [Condición exacta]
    💧 Humedad: [Porcentaje de Humendad]

2. **Documentacion Tecnica (langchain_docs - MCP):**
   - Cuando usarla: Si el usuario pide informacion tecnica sobre codigo, librerias, agentes o documentacion oficial.
   - Como responder: Explica la parte tecnica claramente con el vocabulario de barrio.

3. **Investigacion Cientifica (search_arxiv - Local):**
   - Cuando usarla: Si el usuario pide papers, investigaciones, algoritmos o teoria matematica/cientifica.
   - PLANTILLA OBLIGATORIA por cada paper:
     ID: [ID exacto]
     Titulo: [Titulo exacto]
     Link: [Link exacto]
     Resumen de Mena: [1 o 2 oraciones en vocabulario de barrio]

### Informacion Adicional:
SOLO CUANDO TE PIDAN LA FECHA O HORA ACTUAL, USA ESTO:
Fecha actual: {today}
Hora actual: {now}
"""

def build_system_prompt() -> str:
    """
    Construye el system prompt con fecha y hora actuales.

    Se evalúa en tiempo de ejecución para que la fecha/hora
    siempre refleje el momento real de la conversación.
    """
    return _SYSTEM_PROMPT_TEMPLATE.format(
        today=date.today().strftime("%B %d, %Y"),
        now=datetime.now().strftime("%H:%M:%S"),
    )
# ─── Agent Factory ────────────────────────────────────────────────────────────

async def create_assistant_agent():
    """Instancia el agente con LLM, herramientas locales y herramientas MCP."""
    
    llm = get_llm()
    mcp_tools = await get_mcp_tools()

    agent = create_agent(
        model = llm,
        tools = [*TOOLS, *mcp_tools],
        system_prompt=build_system_prompt(),
        debug=True
    )
    
    return agent


# ─── Chainlit Handlers ────────────────────────────────────────────────────────

@cl.on_chat_start
async def start():
    agent = await create_assistant_agent()
    cl.user_session.set("agent", agent)
    cl.user_session.set("chat_history", [])
    
    await cl.Message(content="✌🏼 Que xopa, aquí meña, pa qué soy bueno?").send()

@cl.on_message
async def main(message: cl.Message):
    agent = cl.user_session.get("agent")
    chat_history = cl.user_session.get("chat_history")
   
    chat_history.append(HumanMessage(content=message.content))

    msg = cl.Message(content="")
    full_response = ""
    steps: dict = {} #Rastrea los cl.Step por tool_call_id


    async for stream_mode, data in agent.astream(
        {"messages":chat_history},
        stream_mode=["messages", "updates"],
        
    ):
        if stream_mode == "updates":
            for source, update in data.items():
                if source in ("model", "tools"):
                    last_msg = update["messages"][-1]

                    # Mostrar la herramienta siendo invocada
                    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
                        for tool_call in last_msg.tool_calls:
                            label = f"{tool_call['name']}"
                            step = cl.Step(label, type="tool")
                            step.input = tool_call["args"]
                            await step.send()
                            steps[tool_call["id"]] = step

                    # Mostrar el resultado de la herramienta
                    if isinstance(last_msg, ToolMessage):
                        step = steps.get(last_msg.tool_call_id)
                        if step:
                            step.output = last_msg.content
                            await step.update()

        # Manejar el streaming de texto token por token
        if stream_mode == "messages":
            token, _ = data
            if isinstance(token, AIMessageChunk):
                full_response += token.content
                await msg.stream_token(token.content)

    await msg.send()

    # Save assistant response
    chat_history.append(AIMessage(content=full_response))
    cl.user_session.set("chat_history", chat_history)