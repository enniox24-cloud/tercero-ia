import json
import time
import re
import os
import sqlite3
from backend.llm import LLM
from backend.memory import MemoryManager
from backend.tools import run_tool
from backend.plugins.voice import VoicePlugin
from backend.automotive import AutomotiveDiagnostic

class TerceroCore:
    def __init__(self):
        self.llm = LLM()
        self.memory = MemoryManager()
        self.voice = VoicePlugin()
        self.auto_diag = AutomotiveDiagnostic()
        self.db_path = "tercero_memory.db"
        self.files_dir = os.path.join(os.getcwd(), "uploads", "files")

    def _recuperar_historial_sqlite(self, user_id: str, limite: int = 15) -> list:
        try:
            if not os.path.exists(self.db_path): return []
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT role, content FROM historial_chat WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limite))
            filas = cursor.fetchall()
            conn.close()
            return [{"role": f[0], "content": f[1]} for f in reversed(filas)]
        except: return []

    def chat(self, user_id: str, message: str) -> dict:
        try:
            history = self._recuperar_historial_sqlite(user_id, limite=16)
            memory = self.memory.recall(user_id)
            system_content = f"Eres Tercero OS. Información de usuario: {memory}. {self.llm.system_prompt}."
            
            # Procesamiento de mensajes y herramientas
            messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": message}]
            answer = self.llm.chat(messages)

            # Audio y Telemetría
            audio_filename = f"response_{int(time.time())}.mp3"
            self.voice.texto_a_voz(answer, filename=audio_filename)

            return {
                "text": answer, 
                "audio_file": audio_filename,
                "telemetry_mode": "BATTERY", 
                "telemetry_status": "NORMAL"
            }
        except Exception as e:
            return {"text": f"Error en el núcleo: {str(e)}", "audio_file": None}
