# backend/llm.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class LLM:

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("[ADVERTENCIA TÉCNICA]: GROQ_API_KEY no detectada en el entorno.")

        self.client = None
        self._inicializar_cliente()

        # =====================================================================
        # POOL DE MODELOS REFORZADO (SISTEMA DE REDUNDANCIA TOTAL)
        # =====================================================================
        # Si uno falla, el sistema rota automáticamente al siguiente de la lista
        self.model_pool = [
            "llama-3.3-70b-versatile",  # El mejor: Máxima lógica, ideal para programación y mecatrónica
            "llama-3.1-70b-versatile",  # Respaldo de alta capacidad
            "llama-3.1-8b-instant",     # Ultra-veloz para respuestas inmediatas
            "llama3-70b-8192",          # Clásico de alta fidelidad 
            "llama3-8b-8192"            # El tanque ligero (nunca falla)
        ]
        
        # El "Cerebro" y directiva de Tercero
        self.system_prompt = (
            "Eres 'Tercero', un asistente de inteligencia artificial avanzado y personalizado. "
            "Fuiste diseñado con un enfoque de alta tecnología, robótica, programación e ingeniería. "
            "Tus respuestas deben ser increíblemente eficientes, inteligentes, profesionales y con un sutil "
            "toque tecnológico y futurista. Ayuda a tu creador con código, análisis de datos y control "
            "del sistema operativo con la máxima precisión matemática y lógica."
        )

    def _inicializar_cliente(self):
        if not self.client and self.api_key:
            self.client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=self.api_key
            )

    def chat(self, messages):
        if not self.api_key:
            self.api_key = os.getenv("GROQ_API_KEY")
        self._inicializar_cliente()

        if not self.client:
            return "Error: Canal cognitivo no configurado (Falta GROQ_API_KEY en Render)."

        contexto_completo = [{"role": "system", "content": self.system_prompt}] + messages
        
        # Bucle de resiliencia: recorre los modelos hasta que uno responda con éxito
        for modelo_actual in self.model_pool:
            try:
                response = self.client.chat.completions.create(
                    model=modelo_actual,
                    messages=contexto_completo,
                    temperature=0.5
                )
                # Si funciona, rompemos el ciclo y entregamos la respuesta
                return response.choices[0].message.content
            except Exception as e:
                print(f"[REDUNDANCIA]: Modelo {modelo_actual} no disponible o denegado. Buscando respaldo... Detalle: {str(e)}")
                continue
        
        return "FALLO CRÍTICO GLOBAL: Ningún modelo de la infraestructura de Groq respondió. Revisa la validez de tu API Key."


# Inicialización de la instancia global segura
try:
    _instancia_global_llm = LLM()
except Exception as e:
    print(f"[ADVERTENCIA]: Error en arranque de llm.py: {e}")
    _instancia_global_llm = None


def ask_llm(prompt: str) -> str:
    """Función rápida de inyección directa desde el núcleo."""
    try:
        global _instancia_global_llm
        if not _instancia_global_llm:
            _instancia_global_llm = LLM()
            
        formato_mensajes = [{"role": "user", "content": prompt}]
        return _instancia_global_llm.chat(formato_mensajes)
    except Exception as e:
        return f"Error en ejecución ask_llm: {str(e)}"
