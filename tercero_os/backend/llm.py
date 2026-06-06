# backend/llm.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class LLM:

    def __init__(self):
        # Intentamos obtener la API key desde las variables de entorno de Render o .env
        self.api_key = os.getenv("GROQ_API_KEY")

        if not self.api_key:
            # En lugar de levantar una excepción fatal que tire el servidor, 
            # guardamos el estado para inicialización tardía (Lazy Loading) en Render.
            print("[ADVERTENCIA TÉCNICA]: No se encontró GROQ_API_KEY en las variables de entorno.")

        self.client = None
        self._inicializar_cliente()

        # =====================================================================
        # MODELOS OFICIALES Y ACTIVOS DE GROQ (EVITA EL ERROR 404)
        # =====================================================================
        self.model = "llama-3.1-8b-instant"       # Modelo principal ultra-rápido
        self.fallback_model = "llama3-8b-8192"   # Modelo de respaldo por si el principal se satura
        
        # El "Cerebro" y directiva de Tercero
        self.system_prompt = (
            "Eres 'Tercero', un asistente de inteligencia artificial avanzado y personalizado. "
            "Fuiste diseñado con un enfoque de alta tecnología, robótica, programación e ingeniería. "
            "Tus respuestas deben ser increíblemente eficientes, inteligentes, profesionales y con un sutil "
            "toque tecnológico y futurista. Ayuda a tu creador con código, análisis de datos y control "
            "del sistema operativo con la máxima precisión matemática y lógica."
        )

    def _inicializar_cliente(self):
        """Inicializa de forma segura el cliente de OpenAI/Groq si no se ha hecho."""
        if not self.client and self.api_key:
            self.client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=self.api_key
            )

    def chat(self, messages):
        # Intentar re-inicializar si la llave se cargó después del arranque
        if not self.api_key:
            self.api_key = os.getenv("GROQ_API_KEY")
        self._inicializar_cliente()

        if not self.client:
            return "Error: Canal de comunicación de Tercero no configurado (Falta GROQ_API_KEY)."

        # Inyectamos el system prompt al inicio del hilo de conversación para fijar su identidad
        contexto_completo = [{"role": "system", "content": self.system_prompt}] + messages
        
        try:
            # Intento con el modelo principal estructurado
            response = self.client.chat.completions.create(
                model=self.model,
                messages=contexto_completo,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[REPARACIÓN BACKEND]: Anomalía con el modelo principal: {str(e)}. Activando contingencia...")
            try:
                # Intento de contingencia inmediata con el modelo de respaldo estable
                response = self.client.chat.completions.create(
                    model=self.fallback_model,
                    messages=contexto_completo,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e_critico:
                return f"Fallo crítico en matriz cognitiva de Tercero OS. Detalle: {str(e_critico)}"


# Inicializamos la instancia global una sola vez para ahorrar memoria y aumentar la velocidad
# Usamos un bloque de contingencia pasiva para que main.py pueda arrancar siempre sin bloquearse.
try:
    _instancia_global_llm = LLM()
except Exception as e:
    print(f"[ADVERTENCIA TÉCNICA]: No se pudo inicializar el modelo Groq: {e}")
    _instancia_global_llm = None


def ask_llm(prompt: str) -> str:
    """Función rápida para llamadas directas desde otros módulos o herramientas."""
    try:
        global _instancia_global_llm
        # Si por alguna anomalía de memoria la instancia falló en el arranque, intentamos recrearla en caliente
        if not _instancia_global_llm:
            _instancia_global_llm = LLM()
            
        if not _instancia_global_llm or not os.getenv("GROQ_API_KEY"):
            return "Error: El motor de Tercero no está inicializado (Falta API Key)."
            
        formato_mensajes = [{"role": "user", "content": prompt}]
        return _instancia_global_llm.chat(formato_mensajes)
    except Exception as e:
        return f"Error en ejecución ask_llm: {str(e)}"
