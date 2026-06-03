import json
import time
import re
import os
from backend.llm import LLM
from backend.memory import MemoryManager
from backend.tools import run_tool
from backend.plugins.voice import VoicePlugin

class TerceroCore:
    def __init__(self):
        self.llm = LLM()
        self.memory = MemoryManager()
        self.voice = VoicePlugin()
        self.histories = {}

    def chat(self, user_id: str, message: str) -> dict:
        try:
            if user_id not in self.histories:
                self.histories[user_id] = []

            history = self.histories[user_id]
            memory = self.memory.recall(user_id)

            system_message = {
                "role": "system",
                "content": f"Eres Tercero OS. Eres un sistema operativo inteligente. Memoria: {memory}. {self.llm.system_prompt}."
            }

            messages = [system_message] + history[-15:] + [{"role": "user", "content": message}]
            answer = self.llm.chat(messages)

            try:
                match = re.search(r"\{.*\}", answer, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if "tool" in parsed:
                        res = run_tool(parsed["tool"], parsed.get("query", ""))
                        answer = self.llm.chat([
                            {"role": "system", "content": f"Resultado de herramienta: {res}. Explícalo al usuario."},
                            {"role": "user", "content": message}
                        ])
            except Exception:
                pass

            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": answer})

            # Generación de voz con ruta absoluta para evitar errores en Render
            audio_filename = f"response_{int(time.time())}.mp3"
            save_path = os.path.join("uploads", audio_filename)
            self.voice.texto_a_voz(answer, filename=save_path)

            return {"text": answer, "audio_file": audio_filename}

        except Exception as e:
            return {"text": f"Error en el núcleo: {str(e)}", "audio_file": None}
