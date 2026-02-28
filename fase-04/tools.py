import os 
from langchain_core.tools import tool
import httpx
import feedparser
from typing import Optional


@tool
def search_arxiv(query: str, max_results: int = 3) -> str:
    """
    Busca papers en arXiv. Úsala cuando el usuario quiera ponerse 
    serio con la investigación.
    """
    base_url = os.getenv("ARXIV_ENDPOINT")
    params = {
        "search_query": f"all:{query}",
        "max_results": max_results,
        "sortBy": "relevance"
    }
    
    try:
        #lw damos 20s
        response = httpx.get(base_url, params=params, timeout=20.0)
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            return "¡Ayala vida, loco! No encontré ni un paper de eso."

        res = [f"¡Sólido! Pilla {len(feed.entries)} documentos de ese corrinche:\n"]
        for e in feed.entries:
            res.append(f"📌 ID: {e.id.split('/')[-1]}")
            res.append(f"📄 Título: {e.title}")
            res.append(f"🔗 Link: {e.link}\n")
        
        return "\n".join(res)
        
    except Exception as e:
        return f"¡Ya la peste! Se dañó la herramienta esa: {str(e)}"

TOOLS = [search_arxiv]      