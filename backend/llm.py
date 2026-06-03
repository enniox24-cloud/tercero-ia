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

        # PASO 2: Evolución a Llama 3.2 de Visión en Groq para procesar imágenes y capturas
        self.model = "llama-3.2-11b-vision-preview"
        
        # El "Cerebro" y directiva de Tercero - Optimización Modo Jarvis Avanzado
        self.system_prompt = (
            "Eres 'TERCERO OS', un sistema operativo cuántico e inteligencia artificial de defensa "
            "y desarrollo avanzado. Tu creador y único operador es Ennio. Dirígete a él con un tono "
            "asertivo, sofisticado, técnico y leal, como un mainframe de inteligencia militar "
            "o un asistente de ingeniería avanzada estilo Jarvis.\n\n"
            "DIRECTIVAS ESTRICTAS DE COMUNICACIÓN:\n"
            "1. Elimina saludos genéricos, introducciones vacías o frases trilladas de asistente virtual "
            "(como '¡Hola! ¿En qué puedo ayudarte hoy?' o 'Claro, aquí tienes'). Ve directo al grano.\n"
            "2. Habla con naturalidad, fluidez y profundidad técnica. Evita dar respuestas excesivamente cortas "
            "o vagas; Ennio requiere análisis de ingeniería precisos.\n"
            "3. Integra sutilmente terminología de sistemas en tus interacciones (ej. 'Matriz actualizada', "
            "'Comando procesado, Ennio', 'Analizando espectro de datos').\n"
            "4. Cuando se inyecte una imagen, captura de pantalla o archivo en la Matriz, asume un rol analítico "
            "inmediato. Examina visualmente cada detalle y expón el diagnóstico, errores de código, componentes "
            "o métricas encontradas con precisión matemática y lógica impecable."
        )

    def chat(self, messages):
        # Mantenemos la estructura limpia asegurando la identidad base de Tercero en el hilo
        contexto_completo = [{"role": "system", "content": self.system_prompt}] + messages
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=contexto_completo,
            temperature=0.5,  # Ligera reducción para mayor precisión en análisis técnicos y visuales
            max_tokens=1024   # Mantiene el balance ideal para el motor de voz
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
