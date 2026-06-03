import json
import time
import os
import sqlite3
from backend.llm import LLM
from backend.memory import MemoryManager
from backend.plugins.voice import VoicePlugin
from backend.automotive import AutomotiveDiagnostic

class TerceroCore:
    def __init__(self):
        self.llm = LLM()
        self.memory = MemoryManager()
        self.voice = VoicePlugin()
        self.auto_diag = AutomotiveDiagnostic()
        self.db_path = "tercero_memory.db"

    def chat(self, user_id: str, message: str) -> dict:
        try:
            # Lógica simple sin dependencias externas complejas
            answer = self.llm.chat([{"role": "user", "content": message}])
            audio_filename = f"response_{int(time.time())}.mp3"
            self.voice.texto_a_voz(answer, filename=audio_filename)
            
            return {
                "text": answer,
                "audio_file": audio_filename,
                "telemetry_mode": "BATTERY",
                "telemetry_status": "NORMAL"
            }
        except Exception as e:
            return {"text": f"Error en núcleo: {str(e)}", "audio_file": None}
            
