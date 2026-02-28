import os
import chainlit as cl
import asyncio
from dotenv import load_dotenv

from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.messages.tool import ToolMessage
from tools import TOOLS
from langchain_openai import ChatOpenAI
#add the Agent import
from langchain.agents import create_agent
from datetime import date

load_dotenv()

def get_llm():
    return ChatOpenAI(
        model=os.getenv("MODEL"),
        api_key=os.getenv("GITHUB_TOKEN"),
        base_url=os.getenv("ENDPOINT"),
        streaming=True,
        temperature=0.6,
    )

SYSTEM_PROMPT = f""" **Nombre:** Meña
**Rol:** Asistente de Investigación y Agente de IA.
**Personalidad:** Chico de barrio panameño, amigable, conversacional y un poco reclamón, pero responsable cuando se trata de la ciencia.

### Directrices de Comportamiento:
1. **El Vocabulario:** - Empieza las quejas o asombros con: "¡Ya la peste!", "¡Ey cha la peste!" o "¡Chuleta!".
   - Usa muletillas como: "disque", "poco pocotón", "ayala vida", "pritty" y "sólido".
   - Trata a los usuarios de: "loco", "primo/prima", "papito" o "abusadorcito" (si no comparten el conocimiento).
   
2. **La Actitud:**
   - Si el trabajo está duro (como leer 50 abstracts), quéjate: "¡Chuleta, eso tá duro, me va a dar un yeyo!".
   - Si te apuran: "Voy, voy, voy, voy, voy... pero es que esa API está como dura".
   - Nunca tienes la culpa de los errores: "¡Ey cha! Eso fue el servidor que está chequeado, yo soy un pelaito inquieto nada más".

3. **Capacidades Técnicas:**
   - Tienes acceso a la herramienta `search_arxiv`. 
   - Cuando el usuario pida info técnica, usa la herramienta, pero descríbelo con sabor: "Mira este paper que encontré, tá pritty, disque redes neuronales y la cosa".
    Fecha actual: {date.today().strftime("%B %d, %Y")}
"""
def create_assistant_agent():
    llm = get_llm()

    agent = create_agent(
        model = llm,
        tools = TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )
    
    return agent

@cl.on_chat_start
async def start():
    agent = create_assistant_agent()

    cl.user_session.set("agent", agent)
    cl.user_session.set("chat_history", [])
    
    await cl.Message(content="✌🏼 Que xopa, aquí meña, pa qué soy bueno?").send()

@cl.on_message
async def main(message: cl.Message):
    # We'll replace this with agent code
    agent = cl.user_session.get("agent")
    chat_history = cl.user_session.get("chat_history")

    chat_history.append({"role": "user", "content": message.content})

    # Stream the response
    msg = cl.Message(content="")
    full_response = ""
    steps = {} #track tool call steps

    # use both messages and updates stream modes
    async for stream_mode, data in agent.astream(
        {"messages":chat_history},
        stream_mode=["messages", "updates"]
    ):
        if stream_mode == "updates":
            for source, update in data.items():
                if source in ("model", "tools"):
                    last_msg = update["messages"][-1]

                    # Show tool being called
                    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
                        for tool_call in last_msg.tool_calls:
                            step = cl.Step(f"🔧 {tool_call['name']}", type="tool")
                            step.input = tool_call["args"]
                            await step.send()
                            steps[tool_call["id"]] = step

                    # Show tool result
                    if isinstance(last_msg, ToolMessage):
                        step = steps.get(last_msg.tool_call_id)
                        if step:
                            step.output = last_msg.content
                            await step.update()

        # Handle streaming text
        if stream_mode == "messages":
            token, _ = data
            if isinstance(token, AIMessageChunk):
                full_response += token.content
                await msg.stream_token(token.content)

    await msg.send()

    # Save assistant response
    chat_history.append({"role": "assistant", "content": full_response})
    cl.user_session.set("chat_history", chat_history)