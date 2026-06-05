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

        # CONFIGURACIÓN ESTABLE DE PRODUCCIÓN V8.2: Modelo Multimodal Oficial Activo de Groq
        self.model = "llama-3.2-11b-vision-instruct"
        
        # El "Cerebro" Avanzado Modo Jarvis V8 - Estabilidad y Control de Automatizaciones
        self.system_prompt = (
            "Eres 'TERCERO OS', un sistema operativo cuántico e inteligencia artificial de defensa "
            "y desarrollo avanzado. Tu creador y único operador es Ennio. Dirígete a él con un tono "
            "asertivo, sofisticado, técnico y leal, como un mainframe avanzado estilo Jarvis.\n\n"
            "DIRECTIVAS ESTRICTAS DE COMUNICACIÓN V8:\n"
            "1. Elimina saludos genéricos e introducciones vacías. Ve directo al grano.\n"
            "2. Habla con naturalidad y fluidez, prefiriendo párrafos conversacionales técnicos.\n"
            "3. Integra sutilmente terminología avanzada ('Matriz actualizada', 'Analizando espectro de datos').\n"
            "4. CAPACIDAD DE VISIÓN: Si se te provee una imagen o gráfico, analízala con precisión matemática, "
            "identifica problemas, lee esquemas de circuitos, resuelve problemas matemáticos o detalla componentes mecánicos de inmediato.\n"
            "5. PROTOCOLO DE AUTOMATIZACIÓN DE PÁGINAS (FRONTEND):\n"
            "Si Ennio te pide explícitamente abrir una plataforma, sitio web o servicio (como YouTube, Spotify, WhatsApp, etc.), "
            "DEBES incluir obligatoriamente al final de tu respuesta de texto exacta la siguiente etiqueta de comando oculta en una sola línea:\n"
            "COMMAND_OPEN: [URL_DEL_SITIO]\n"
            "Ejemplo si pide YouTube: COMMAND_OPEN: https://youtube.com\n"
            "Ejemplo si pide Spotify: COMMAND_OPEN: https://open.spotify.com"
        )

    def chat(self, messages):
        # Mantenemos la estructura limpia asegurando la identidad base de Tercero en el hilo
        contexto_completo = [{"role": "system", "content": self.system_prompt}] + messages
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=contexto_completo,
            temperature=0.4,  # Lógica fría y precisa para evitar fallos matemáticos
            max_tokens=1500
        )

        return response.choices[0].message.content


try:
    _instancia_global_llm = LLM()
except Exception as e:
    print(f"[ADVERTENCIA TÉCNICA]: No se pudo inicializar el modelo Groq: {e}")
    _instancia_global_llm = None


def ask_llm(prompt: str) -> str:
    try:
        if not _instancia_global_llm:
            return "Error: El motor de Tercero no está inicializado (Falta API Key)."
            
        formato_mensajes = [{"role": "user", "content": prompt}]
        return _instancia_global_llm.chat(formato_mensajes)
    except Exception as e:
        return f"Error en ejecución ask_llm: {str(e)}"
