# LangChain + Chainlit · Guía paso a paso para construir un agente conversacional

Este repositorio es un **walkthrough progresivo** que lleva al desarrollador desde cero —configurar el entorno con `uv`— hasta tener un agente conversacional completo con herramientas locales e integración MCP corriendo en Chainlit.

Cada fase es un programa independiente y funcional. Puedes leer el código de cada carpeta para ver exactamente qué cambió respecto a la fase anterior.

---

## Tabla de contenidos

1. [Stack tecnológico](#stack-tecnológico)
2. [Requisitos previos](#requisitos-previos)
3. [Fase 1 — Configurar el entorno con uv](#fase-1--configurar-el-entorno-con-uv)
4. [Fase 2 — Probar la conexión con GitHub Models](#fase-2--probar-la-conexión-con-github-models)
5. [Fase 3 — Chat básico con Chainlit y LangChain](#fase-3--chat-básico-con-chainlit-y-langchain)
6. [Fase 4 — Agente con herramientas (arXiv)](#fase-4--agente-con-herramientas-arxiv)
7. [Fase 5 — Agente completo con MCP y más herramientas](#fase-5--agente-completo-con-mcp-y-más-herramientas)
8. [Variables de entorno — referencia completa](#variables-de-entorno--referencia-completa)
9. [Estructura del repositorio](#estructura-del-repositorio)

---

## Stack tecnológico

| Capa | Herramienta |
|---|---|
| UI conversacional | [Chainlit](https://docs.chainlit.io) |
| Orquestación LLM | [LangChain](https://python.langchain.com) |
| Modelo de lenguaje | [GitHub Models](https://github.com/marketplace/models) vía API compatible con OpenAI |
| Herramientas externas | arXiv (feed RSS), WeatherAPI |
| Protocolo de herramientas remotas | [MCP](https://modelcontextprotocol.io) — `langchain-mcp-adapters` |
| Gestión de entorno | [uv](https://docs.astral.sh/uv/) |

---

## Requisitos previos

- Python 3.12 o superior
- [uv](https://docs.astral.sh/uv/getting-started/installation/) instalado
- Una cuenta en GitHub con acceso a [GitHub Models](https://github.com/marketplace/models)
- (Opcional, Fase 5) API key de [WeatherAPI](https://www.weatherapi.com/)

---

## Fase 1 — Configurar el entorno con uv

### ¿Qué es uv?

`uv` es un gestor de paquetes y entornos virtuales para Python, escrito en Rust, que reemplaza en un solo comando a `pip`, `venv` y `pip-tools`. Es varias veces más rápido que sus equivalentes tradicionales.

### 1.1 Inicializar el proyecto

```bash
# Crear el directorio del proyecto
mkdir langchain-chainlit-agent-walkthrough
cd langchain-chainlit-agent-walkthrough

# Inicializar el proyecto con uv (crea pyproject.toml)
uv init
```

`uv init` genera un `pyproject.toml` mínimo. Puedes editarlo para añadir metadatos:

```toml
[project]
name = "langchain-chainlit-agent-demo"
version = "0.1.0"
description = "Agente conversacional con LangChain y Chainlit"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []
```

### 1.2 Crear el entorno virtual

```bash
uv venv
```

Esto crea la carpeta `.venv/` en el directorio raíz. No necesitas activarlo manualmente; `uv run` lo usa de forma transparente.

### 1.3 Instalar las dependencias

Añade las dependencias al `pyproject.toml` y luego sincroniza:

```toml
dependencies = [
    "arxiv>=2.4.0",
    "chainlit>=2.0.0",
    "fastmcp>=3.0.2",
    "feedparser>=6.0.12",
    "langchain>=0.3.0",
    "langchain-mcp-adapters>=0.2.1",
    "langchain-openai>=0.3.0",
    "mcp>=1.0.0",
    "python-dotenv>=1.0.0",
]
```

```bash
uv sync
```

También puedes instalar paquetes directamente con `uv add`:

```bash
uv add chainlit langchain langchain-openai python-dotenv
```

### 1.4 Crear el archivo `.env`

Crea un archivo `.env` en la raíz del proyecto (nunca lo subas a git):

```bash
# .env
GITHUB_TOKEN=ghp_tu_token_aqui
MODEL=gpt-4o-mini
ENDPOINT=https://models.inference.ai.azure.com
```

### 1.5 Configurar `.gitignore`

```gitignore
# Python
__pycache__/
*.py[oc]
build/
dist/
*.egg-info

# uv
.python-version
uv.lock

# Entorno virtual
.venv/

# Secretos
.env

# Chainlit
.chainlit/
```

---

## Fase 2 — Probar la conexión con GitHub Models

**Carpeta:** `fase-02/`
**Objetivo:** Verificar que el token y el endpoint de GitHub Models funcionan antes de construir la UI.

### Conceptos introducidos

- Cargar variables de entorno con `python-dotenv`
- Instanciar `ChatOpenAI` apuntando a GitHub Models
- Invocar el modelo con una consulta simple

### Código clave (`fase-02/test_github_models.py`)

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("MODEL"),
    api_key=os.getenv("GITHUB_TOKEN"),
    base_url=os.getenv("ENDPOINT"),
    temperature=0.5
)

response = llm.invoke("¿Cuál es la capital de Veraguas en Panamá?")
print(response)
```

`ChatOpenAI` de LangChain acepta un `base_url` personalizado, lo que permite apuntar a cualquier API compatible con OpenAI —como GitHub Models— sin cambiar el código de orquestación.

### Cómo ejecutar

```bash
cd fase-02
uv run python test_github_models.py
```

Salida esperada: la respuesta del modelo impresa en consola.

---

## Fase 3 — Chat básico con Chainlit y LangChain

**Carpeta:** `fase-03/`
**Objetivo:** Construir una interfaz de chat web con historial de conversación y streaming de tokens.

### Conceptos introducidos

- Decoradores de Chainlit: `@cl.on_chat_start`, `@cl.on_message`
- Sesión de usuario con `cl.user_session`
- Historial de mensajes con `HumanMessage`, `AIMessage`, `SystemMessage` de LangChain
- Streaming token a token con `llm.astream()`
- Encapsular el LLM en un módulo reutilizable (`llm_handler`)

### Estructura de archivos

```
fase-03/
├── app.py                        # Punto de entrada de Chainlit
├── chainlit.md                   # Pantalla de bienvenida
├── llm_handler/
│   ├── __init__.py
│   └── llm_handler.py            # Wrapper del cliente LLM
└── ai_interface/
    └── messages_interface.py     # Handlers on_chat_start / on_message
```

### Cómo funciona el historial

En cada sesión Chainlit, se guarda una lista de mensajes en `cl.user_session`. Cada turno añade el mensaje del usuario y la respuesta del modelo, preservando el contexto completo de la conversación:

```python
# Inicializar con el system prompt
cl.user_session.set("chat_history", [SystemMessage(content=SYSTEM_PROMPT)])

# En cada mensaje: añadir usuario → respuesta del modelo
chat_history.append(HumanMessage(content=message.content))
# ... streaming ...
chat_history.append(AIMessage(content=full_response))
```

### Streaming token a token

```python
msg = cl.Message(content="")

async for token in llm.astream(chat_history):
    if token.content:
        await msg.stream_token(token.content)

await msg.send()
```

`msg.stream_token()` envía cada fragmento al navegador en tiempo real, dando la experiencia de escritura progresiva.

### Cómo ejecutar

```bash
cd fase-03
uv run chainlit run app.py -w
```

La flag `-w` activa el modo watch (recarga automática al guardar). Chainlit abrirá el navegador en `http://localhost:8000`.

---

## Fase 4 — Agente con herramientas (arXiv)

**Carpeta:** `fase-04/`
**Objetivo:** Convertir el chat en un agente capaz de usar herramientas externas; en este caso, buscar papers en arXiv.

### Conceptos introducidos

- `@tool` de LangChain para definir herramientas
- `create_agent` para construir un agente React
- Streaming dual `["messages", "updates"]` para ver tanto el texto generado como el estado interno del agente
- `cl.Step` para mostrar en la UI cuándo y con qué argumentos se llama una herramienta

### Definir una herramienta con `@tool`

```python
from langchain_core.tools import tool
import httpx, feedparser

@tool
def search_arxiv(query: str, max_results: int = 3) -> str:
    """Busca papers en arXiv. El docstring es la descripción que lee el LLM."""
    base_url = os.getenv("ARXIV_ENDPOINT")
    params = {"search_query": f"all:{query}", "max_results": max_results, "sortBy": "relevance"}
    response = httpx.get(base_url, params=params, timeout=20.0)
    feed = feedparser.parse(response.text)
    # ... formatear y devolver resultados
```

El decorador `@tool` convierte la función Python en un objeto `Tool` que el agente puede invocar automáticamente cuando lo necesita. El docstring es crucial: es la descripción que el LLM lee para decidir cuándo usar la herramienta.

### Crear el agente

```python
from langchain.agents import create_agent

agent = create_agent(
    model=llm,
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT,
)
```

### Streaming con visibilidad de herramientas

El agente produce dos tipos de eventos en el stream:

```python
async for stream_mode, data in agent.astream(
    {"messages": chat_history},
    stream_mode=["messages", "updates"]
):
    if stream_mode == "updates":
        # Detectar llamadas a herramientas y sus resultados
        last_msg = update["messages"][-1]
        if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
            step = cl.Step(f"🔧 {tool_call['name']}", type="tool")
            await step.send()
        if isinstance(last_msg, ToolMessage):
            step.output = last_msg.content
            await step.update()

    if stream_mode == "messages":
        # Texto generado por el modelo
        token, _ = data
        await msg.stream_token(token.content)
```

`cl.Step` crea en la UI un componente colapsable que muestra la herramienta invocada, sus argumentos de entrada y el resultado obtenido.

### Variables de entorno adicionales

```bash
ARXIV_ENDPOINT=https://export.arxiv.org/api/query
```

### Cómo ejecutar

```bash
cd fase-04
uv run chainlit run app.py -w
```

---

## Fase 5 — Agente completo con MCP y más herramientas

**Carpeta:** `fase-05/`
**Objetivo:** Extender el agente con una segunda herramienta local (clima) y conectarlo a un servidor MCP remoto (documentación de LangChain).

### Conceptos introducidos

- `MultiServerMCPClient` de `langchain-mcp-adapters` para consumir herramientas MCP
- Combinar herramientas locales y remotas en el mismo agente
- Validación explícita de variables de entorno al inicializar el LLM
- System prompt con plantilla y valores dinámicos (fecha/hora actuales)

### Agregar una herramienta de clima

```python
@tool
def get_weather(city: str) -> str:
    """Obtiene el clima actual de una ciudad."""
    api_key = os.getenv("WEATHER_API_KEY")
    endpoint = os.getenv("WEATHER_ENDPOINT")
    response = httpx.get(endpoint, params={"key": api_key, "q": city}, timeout=10.0)
    data = response.json()
    return (
        f"Clima para {data['location']['name']}, {data['location']['country']}:\n"
        f"🌡️ Temperatura: {data['current']['temp_c']}°C\n"
        f"☁️ Condición: {data['current']['condition']['text']}\n"
        f"💧 Humedad: {data['current']['humidity']}%"
    )
```

### Conectar a un servidor MCP

MCP (Model Context Protocol) permite que servidores externos expongan herramientas sin que tengas que implementarlas localmente.

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

async def get_mcp_tools():
    mcp_client = MultiServerMCPClient(
        {
            "langchain_docs": {
                "transport": "http",
                "url": "https://docs.langchain.com/mcp",
            }
        }
    )
    return await mcp_client.get_tools()
```

`get_tools()` devuelve objetos `Tool` de LangChain directamente, por lo que se combinan con las herramientas locales sin fricción:

```python
agent = create_agent(
    model=llm,
    tools=[*TOOLS, *mcp_tools],   # herramientas locales + MCP
    system_prompt=build_system_prompt(),
)
```

### System prompt dinámico

Para que el agente conozca la fecha y hora actuales sin tener que invocar una herramienta extra:

```python
_TEMPLATE = """
...
Fecha actual: {today}
Hora actual: {now}
"""

def build_system_prompt() -> str:
    return _TEMPLATE.format(
        today=date.today().strftime("%B %d, %Y"),
        now=datetime.now().strftime("%H:%M:%S"),
    )
```

### Validación de variables de entorno

```python
def get_llm():
    required = ["GITHUB_MODEL", "GITHUB_TOKEN", "GITHUB_ENDPOINT"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise EnvironmentError(f"Variables de entorno faltantes: {missing}")
    return ChatOpenAI(...)
```

Validar al inicio de la sesión evita errores silenciosos en el medio de una conversación.

### Variables de entorno adicionales

```bash
WEATHER_API_KEY=tu_api_key_de_weatherapi
WEATHER_ENDPOINT=https://api.weatherapi.com/v1/current.json
```

### Cómo ejecutar

```bash
cd fase-05
uv run chainlit run app.py -w
```

---

## Variables de entorno — referencia completa

Crea un archivo `.env` en la raíz del proyecto con las variables que necesites según la fase:

```bash
# ── GitHub Models (Fases 2-5) ─────────────────────────────────────────────────
GITHUB_TOKEN=ghp_tu_token_aqui
MODEL=gpt-4o-mini                              # Fase 2-4
ENDPOINT=https://models.inference.ai.azure.com # Fase 2-4

# Nombres alternativos usados en Fase 5
GITHUB_MODEL=gpt-4o-mini
GITHUB_ENDPOINT=https://models.inference.ai.azure.com

# ── arXiv (Fases 4-5) ─────────────────────────────────────────────────────────
ARXIV_ENDPOINT=https://export.arxiv.org/api/query

# ── WeatherAPI (Fase 5) ───────────────────────────────────────────────────────
WEATHER_API_KEY=tu_api_key
WEATHER_ENDPOINT=https://api.weatherapi.com/v1/current.json
```

Para obtener un token de GitHub Models:
1. Ve a [github.com/settings/tokens](https://github.com/settings/tokens)
2. Genera un token clásico con los permisos mínimos necesarios
3. Activa el acceso a GitHub Models desde [github.com/marketplace/models](https://github.com/marketplace/models)

---

## Estructura del repositorio

```
.
├── pyproject.toml          # Dependencias y metadatos del proyecto (uv)
├── requirements.txt        # Lista de dependencias (referencia)
├── .gitignore
├── README.md
│
├── fase-02/
│   └── test_github_models.py        # Script de prueba de conexión
│
├── fase-03/
│   ├── app.py                       # Punto de entrada Chainlit
│   ├── chainlit.md                  # Pantalla de bienvenida
│   ├── llm_handler/
│   │   ├── __init__.py
│   │   └── llm_handler.py           # Wrapper ChatOpenAI
│   └── ai_interface/
│       └── messages_interface.py    # Handlers + historial + streaming
│
├── fase-04/
│   ├── app.py                       # Agente con visualización de herramientas
│   ├── chainlit.md
│   └── tools.py                     # Herramienta search_arxiv
│
└── fase-05/
    ├── app.py                       # Agente completo con MCP
    ├── chainlit.md
    └── tools.py                     # search_arxiv + get_weather
```

---

## Progresión de conceptos por fase

| Fase | Novedad principal |
|------|-------------------|
| 1 | Entorno con `uv`, `pyproject.toml`, `.env` |
| 2 | `ChatOpenAI` + GitHub Models + `load_dotenv` |
| 3 | Chainlit UI, `user_session`, historial, streaming con `astream` |
| 4 | `@tool`, `create_agent`, `cl.Step`, streaming dual |
| 5 | `MultiServerMCPClient`, múltiples herramientas, system prompt dinámico |
