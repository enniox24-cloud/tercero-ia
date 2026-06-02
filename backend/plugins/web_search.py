# backend/plugins/web_search.py
import requests

def search(query: str) -> str:
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        # 1. Intentamos capturar el resumen enciclopédico directo
        abstract = data.get("AbstractText")
        if abstract:
            return abstract

        # 2. Extracción profunda de resultados web alternativos
        related_topics = data.get("RelatedTopics", [])
        if related_topics:
            contexto_busqueda = []
            
            for topic in related_topics:
                if len(contexto_busqueda) >= 3:  # Límite de 3 resultados relevantes para no saturar al LLM
                    break
                    
                # Si es un resultado directo, extraemos el texto
                text = topic.get("Text")
                if text:
                    contexto_busqueda.append(text)
                # Si DuckDuckGo agrupó el resultado dentro de un sub-tópico, bajamos un nivel
                elif "Topics" in topic:
                    for sub_topic in topic.get("Topics", []):
                        sub_text = sub_topic.get("Text")
                        if sub_text and len(contexto_busqueda) < 3:
                            contexto_busqueda.append(sub_text)

            if contexto_busqueda:
                return "\n".join(contexto_busqueda)

        return f"No se encontró información o resumen directo en la matriz para: {query}"

    except Exception as e:
        return f"Error en ejecución de búsqueda web: {str(e)}"