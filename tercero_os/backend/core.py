import json
import time
import re
import os
from backend.llm import LLM
from backend.memory import MemoryManager
from backend.tools import run_tool
from backend.plugins.voice import VoicePlugin

# Importación segura de la librería
try:
    from pyngrok import ngrok, conf
except ImportError:
    ngrok = None

class TerceroCore:

    def __init__(self):
        self.llm = LLM()
        self.memory = MemoryManager()
        self.voice = VoicePlugin()
        self.histories = {}
        # Lanzamiento del despliegue a la nube
        self.iniciar_conexion_nube()

    def iniciar_conexion_nube(self):
        """
        Despliega un túnel seguro usando el ejecutable local para evitar errores de red.
        """
        if ngrok:
            try:
                # CORRECCIÓN: Apuntamos directamente al archivo ngrok.exe en la raíz
                # Esto evita que la librería intente descargar nada de internet.
                ruta_local = os.path.join(os.getcwd(), "ngrok.exe")
                conf.get_default().ngrok_path = ruta_local
                
                token_ngrok = "3EYmToslNYVk1EjkT5hweZIOXD8_5PacqPwLLvU3opFNJuzdr"
                ngrok.set_auth_token(token_ngrok)
                
                ngrok.kill() # Limpiamos procesos previos
                tunel_publico = ngrok.connect(5000)
                
                print("\n" + "="*60)
                print(" 🌌 CLOUD DISPATCH: TERCERO EN LA NUBE INTEGRADO")
                print(f" URL DE ACCESO GLOBAL -> {tunel_publico.public_url}")
                print("="*60 + "\n")
                
            except Exception as e:
                print(f"-> [ERROR DE RED]: No se pudo conectar el túnel: {e}")
        else:
            print("-> [ALERTA]: pyngrok no detectado.")

    def chat(self, user_id: str, message: str) -> dict:
        try:
            if user_id not in self.histories:
                self.histories[user_id] = []

            history = self.histories[user_id]
            memory = self.memory.recall(user_id)

            # Directivas del núcleo
            system_message = {
                "role": "system",
                "content": f"Eres Tercero OS. Eres un sistema operativo inteligente. Memoria: {memory}. {self.llm.system_prompt}. Si se requiere hardware/apps, responde SOLO con JSON con 'tool' y 'query'."
            }

            messages = [system_message] + history[-15:] + [{"role": "user", "content": message}]
            answer = self.llm.chat(messages)

            # PROCESADOR DE COMANDOS
            match = re.search(r"\{.*\}", answer, re.DOTALL)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    if "tool" in parsed:
                        res = run_tool(parsed["tool"], parsed.get("query", ""))
                        # IA procesa el resultado del hardware para responder al usuario
                        answer = self.llm.chat([
                            {"role": "system", "content": f"El resultado de la herramienta {parsed['tool']} fue: {res}. Explícalo al usuario."},
                            {"role": "user", "content": message}
                        ])
                except Exception:
                    pass

            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": answer})

            audio_filename = f"response_{int(time.time())}.mp3"
            self.voice.texto_a_voz(answer, filename=audio_filename)

            return {"text": answer, "audio_file": audio_filename}

        except Exception as e:
            return {"text": f"Error crítico en el núcleo: {str(e)}", "audio_file": None}