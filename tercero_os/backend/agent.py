# backend/agent.py
import json
from backend.llm import ask_llm
from backend.memory import save_memory, load_memory
from backend.tools import run_tool

def procesar(prompt: str):
    memoria = load_memory()

    contexto = f"""
Eres Tercero OS, un agente inteligente.

Si necesitas usar una herramienta, responde EXACTAMENTE así:
{{
  "tool": "search",
  "query": "texto"
}}

Herramientas disponibles:
- search

Memoria:
{memoria}

Usuario: {prompt}
"""

    respuesta = ask_llm(contexto)

    # 🧠 DETECTAR JSON TOOL CALL
    try:
        parsed = json.loads(respuesta)

        if "tool" in parsed:
            tool = parsed["tool"]
            query = parsed["query"]

            resultado = run_tool(tool, query)

            final_prompt = f"""
Información obtenida:
{resultado}

Responde al usuario:
{prompt}
"""

            respuesta_final = ask_llm(final_prompt)
            save_memory(prompt, respuesta_final)
            return respuesta_final

    except:
        # si no es tool call, respuesta normal
        save_memory(prompt, respuesta)
        return respuesta