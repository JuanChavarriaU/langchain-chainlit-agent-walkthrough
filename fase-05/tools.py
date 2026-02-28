import os 
from langchain_core.tools import tool
import httpx
import feedparser



@tool
def get_weather(city: str) -> str:
    """
    Obtiene el clima actual de una ciudad.

    Args:
        city: El nombre de la ciudad (ej. "Ciudad de Panamá", "Tokyo")

    Returns:
        Condiciones climáticas actuales.
    """
    api_key = os.getenv("WEATHER_API_KEY")
    endpoint = os.getenv("WEATHER_ENDPOINT")

    if not api_key or not endpoint:
        raise EnvironmentError(
            "Variables de entorno faltantes: WEATHER_API_KEY, WEATHER_ENDPOINT"
        )
    
    try:
        response = httpx.get(
            endpoint,
            params={"key": api_key, "q": city},
            timeout=10.0
        )
        response.raise_for_status()
        data = response.json()
        
        location = data["location"]["name"]
        country = data["location"]["country"]
        temp_c = data["current"]["temp_c"]
        condition = data["current"]["condition"]["text"]
        humidity = data["current"]["humidity"]
        
        return (
            f"Clima para {location}, {country}:\n"
            f"🌡️ Temperatura: {temp_c}°C\n"
            f"☁️ Condición: {condition}\n"
            f"💧 Humedad: {humidity}%"
            )
        
    except httpx.TimeoutException:
        return f"Error: La solicitud para '{city}' tardó demasiado. Intenta de nuevo."
    except httpx.HTTPStatusError as e:
        return f"Error HTTP {e.response.status_code}: No se encontró clima para '{city}'."
    except KeyError as e:
        return f"Error al parsear la respuesta de la API: campo {e} no encontrado."
    except Exception as e:
        return f"Error inesperado: {e}"

@tool
def search_arxiv(query: str, max_results: int = 3) -> str:
    """
    Busca papers en arXiv. Úsala cuando el usuario quiera ponerse 
    serio con la investigación.

    Args:
        query: El término de búsqueda (e.g., "redes neuronales", "transformers")
        max_results: Cuántos resultados mostrar (default: 3)
    returns:
        Una lista de papers encontrados con título, ID y link.    
    """
    base_url = os.getenv("ARXIV_ENDPOINT")

    if not base_url:
        raise EnvironmentError("Variable de entorno faltante: ARXIV_ENDPOINT")

    params = {
        "search_query": f"all:{query}",
        "max_results": max_results,
        "sortBy": "relevance"
    }
    
    try:
        response = httpx.get(base_url, params=params, timeout=20.0)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            return "¡Ayala vida, loco! No encontré ni un paper de eso."

        header = [f"¡Sólido! Pilla {len(feed.entries)} documentos:\n"]
        entries = "\n".join(
            f"📌 ID: {e.id.split('/')[-1]}\n"
            f"📄 Título: {e.title}\n"
            f"🔗 Link: {e.link}"
            for e in feed.entries
        )
        
        return f"{header}\n{entries}"
        
    except httpx.TimeoutException:
        return "¡Ya la peste! arXiv tardó demasiado en responder, primo."
    except httpx.HTTPStatusError as e:
        return f"¡Chuleta! Error HTTP {e.response.status_code} al consultar arXiv."
    except Exception as e:
        return f"¡Ya la peste! Se dañó la herramienta esa: {e}"

# ─── Registro de herramientas disponibles
TOOLS = [search_arxiv, get_weather]      