import time
import os
import sqlite3
import re
from backend.llm import LLM
from backend.memory import MemoryManager
from backend.plugins.voice import VoicePlugin

class TerceroCore:
    def __init__(self):
        self.llm = LLM()
        self.memory = MemoryManager()
        self.voice = VoicePlugin()
        self.db_path = "tercero_memory.db"
        self.files_dir = os.path.join(os.getcwd(), "uploads", "files")

    def chat(self, user_id: str, message: str) -> dict:
        try:
            # Análisis de archivos si el mensaje indica una carga
            contenido_extraido = ""
            if "archivo" in message.lower():
                contenido_extraido = "[Sistema]: Archivo recibido en el Mainframe. Analizando contenido..."

            # Construcción de la respuesta de la IA
            messages = [{"role": "user", "content": f"{message}. Datos extra: {contenido_extraido}"}]
            answer = self.llm.chat(messages)

            # Generación de voz
            audio_filename = f"response_{int(time.time())}.mp3"
            self.voice.texto_a_voz(answer, filename=audio_filename)
            
            return {
                "text": answer,
                "audio_file": f"/uploads/responses/{audio_filename}",
                "telemetry_mode": "BATTERY",
                "telemetry_status": "NORMAL"
            }
        except Exception as e:
            return {"text": f"Error en Tercero Core: {str(e)}", "audio_file": None}
