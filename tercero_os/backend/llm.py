# backend/llm.py
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class LLM:

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            print("[ADVERTENCIA TÉCNICA]: GROQ_API_KEY no detectada.")

        self.client = None
        self._inicializar_cliente()

        # POOL DE MODELOS OFICIALES DE GROQ (Cero modelos de visión obsoletos)
        self.model_pool = [
            "llama-3.3-70b-versatile",  # Principal: Máxima lógica y programación
            "llama-3.1-8b-instant",     # Respaldo 1: Ultra-veloz
            "llama3-70b-8192",          # Respaldo 2: Alta capacidad
            "llama3-8b-8192"            # Respaldo 3: Indestructible
        ]
        
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
            return "Error: Canal cognitivo no configurado (Falta GROQ_API_KEY)."

        # Construcción limpia inyectando las directivas de Tercero OS
        contexto_completo = [{"role": "system", "content": self.system_prompt}] + [
            m for m in messages if m.get("role") != "system"
        ]
        
        for modelo_actual in self.model_pool:
            try:
                response = self.client.chat.completions.create(
                    model=modelo_actual,
                    messages=contexto_completo,
                    temperature=0.5
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"[POOL]: {modelo_actual} no disponible. Saltando... Detalle: {str(e)}")
                continue
        
        return "FALLO CRÍTICO GLOBAL: Ningún modelo de Groq respondió. Revisa tu API Key."

try:
    _instancia_global_llm = LLM()
except Exception as e:
    print(f"[ERROR]: Instancia LLM fallida: {e}")
    _instancia_global_llm = None

def ask_llm(prompt: str) -> str:
    try:
        global _instancia_global_llm
        if not _instancia_global_llm:
            _instancia_global_llm = LLM()
        return _instancia_global_llm.chat([{"role": "user", "content": prompt}])
    except Exception as e:
        return f"Error en ask_llm: {str(e)}"
