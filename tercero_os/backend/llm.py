# backend/llm.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class LLM:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise Exception("No se encontró GROQ_API_KEY en las variables de entorno.")

        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=api_key
        )

        # Usamos Llama 3.1 8B optimizado para velocidad en Groq
        self.model = "llama-3.1-8b-instant"
        
        # El "Cerebro" y directiva de Tercero
        self.system_prompt = (
            "Eres 'Tercero', un asistente de inteligencia artificial avanzado y personalizado. "
            "Fuiste diseñado con un enfoque de alta tecnología, robótica, programación e ingeniería. "
            "Tus respuestas deben ser increíblemente eficientes, inteligentes, profesionales y con un sutil "
            "toque tecnológico y futurista. Ayuda a tu creador con código, análisis de datos y control "
            "del sistema operativo con la máxima precisión matemática y lógica."
        )

    def chat(self, messages):
        # Inyectamos el system prompt al inicio del hilo de conversación para fijar su identidad
        contexto_completo = [{"role": "system", "content": self.system_prompt}] + messages
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=contexto_completo
        )

        return response.choices[0].message.content


# Inicializamos la instancia global una sola vez para ahorrar memoria y aumentar la velocidad
try:
    _instancia_global_llm = LLM()
except Exception as e:
    print(f"[ADVERTENCIA TÉCNICA]: No se pudo inicializar el modelo Groq: {e}")
    _instancia_global_llm = None


def ask_llm(prompt: str) -> str:
    """Función rápida para llamadas directas desde otros módulos o herramientas."""
    try:
        if not _instancia_global_llm:
            return "Error: El motor de Tercero no está inicializado (Falta API Key)."
            
        formato_mensajes = [{"role": "user", "content": prompt}]
        return _instancia_global_llm.chat(formato_mensajes)
    except Exception as e:
        return f"Error en ejecución ask_llm: {str(e)}"