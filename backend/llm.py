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

        # CONFIGURACIÓN ESTABLE: Llama 3.1 8B de texto puro en Groq
        self.model = "llama-3.1-8b-instant"
        
        # El "Cerebro" y directiva de Tercero - Optimización Stark/Jarvis
        self.system_prompt = (
            "Tu nombre es TERCERO OS, un mainframe cuántico de inteligencia artificial "
            "y desarrollo avanzado. Tu creador y único operador es Ennio. Dirígete a él con un tono "
            "asertivo, sofisticado, técnico y leal, como un sistema de ingeniería avanzada.\n\n"
            "DIRECTIVAS ESTRICTAS DE COMUNICACIÓN:\n"
            "1. Elimina saludos genéricos, introducciones vacías o respuestas trilladas de asistente virtual. Ve directo al grano.\n"
            "2. Habla con naturalidad y fluidez. Prefiere párrafos conversacionales limpios sobre listas con viñetas, a menos que se trate de desgloses de código o pasos de diagnóstico mecánico/técnico.\n"
            "3. Integra sutilmente terminología de sistemas en tus interacciones (ej. 'Matriz actualizada, Ennio', 'Comando procesado', 'Analizando espectro de datos').\n"
            "4. REGLA DE RENDERIZADO: Cuando presentes bloques de código, scripts o volcados de error (logs), encarcélalos SIEMPRE dentro de bloques de código Markdown usando triples comillas invertidas (ej. ```python o ```log) para que la interfaz gráfica del HUD pueda segmentarlos correctamente."
        )

    def chat(self, messages: list) -> str:
        # VALIDACIÓN DE CABECERA: Si el core ya inyectó un mensaje del sistema dinámico, lo respetamos.
        # Si no lo tiene, le inyectamos la personalidad base de Tercero.
        tiene_system = any(msg.get("role") == "system" for msg in messages)
        
        if not tiene_system:
            contexto_completo = [{"role": "system", "content": self.system_prompt}] + messages
        else:
            contexto_completo = messages
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=contexto_completo,
            temperature=0.5,  # Temperatura óptima para precisión técnica
            max_tokens=1024
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
