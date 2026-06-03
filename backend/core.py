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
        # Definimos la ruta de la matriz de archivos para poder escanearlos
        self.files_dir = os.path.join(os.getcwd(), "uploads", "files")

    def chat(self, user_id: str, message: str) -> dict:
        try:
            if user_id not in self.histories:
                self.histories[user_id] = []

            history = self.histories[user_id]
            memory = self.memory.recall(user_id)

            # INTERCEPTOR Y EXTRACTOR DE MATRIZ DE ARCHIVOS
            # Si el sistema notifica la carga de un archivo, extraemos su contenido antes de procesar
            contenido_extraido = ""
            match_archivo = re.search(r"El usuario ha cargado el archivo '([^']+)'", message)
            
            if match_archivo:
                nombre_archivo = match_archivo.group(1)
                ruta_completa = os.path.join(self.files_dir, nombre_archivo)
                
                if os.path.exists(ruta_completa):
                    ext = os.path.splitext(nombre_archivo)[1].lower()
                    
                    # Extractor para documentos de texto plano, scripts, códigos o configuraciones
                    if ext in ['.txt', '.py', '.js', '.json', '.html', '.css', '.md']:
                        try:
                            with open(ruta_completa, 'r', encoding='utf-8', errors='ignore') as f:
                                contenido_extraido = f.read(15000) # Leemos los primeros 15k caracteres para no saturar el contexto
                        except Exception as e:
                            contenido_extraido = f"[Fallo al leer texto plano: {str(e)}]"
                            
                    # Estructura de preparación para PDF o Metadatos de Imagen
                    elif ext == '.pdf':
                        # Lógica de extracción nativa de strings legibles o metadatos básicos
                        contenido_extraido = f"[Documento PDF detectado en el Mainframe: '{nombre_archivo}'. Procesando su flujo de datos indexado]."
                    else:
                        contenido_extraido = f"[Archivo binario/Imagen detectado en el Mainframe: '{nombre_archivo}'. Formato listo para indexación]."

            # Si logramos extraer datos del archivo, los inyectamos de forma limpia como contexto del sistema
            system_content = f"Eres Tercero OS. Eres un sistema operativo inteligente. Memoria: {memory}. {self.llm.system_prompt}."
            if contenido_extraido:
                system_content += f"\n\n[DATOS EXTRAÍDOS DE LA MATRIZ DE ARCHIVOS]:\n{contenido_extraido}"

            system_message = {
                "role": "system",
                "content": system_content
            }

            messages = [system_message] + history[-15:] + [{"role": "user", "content": message}]
            answer = self.llm.chat(messages)

            # PROCESADOR DE COMANDOS (TOOLS)
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

            # Generamos el nombre del archivo de audio de forma limpia
            audio_filename = f"response_{int(time.time())}.mp3"
            
            # Forzamos la limpieza automática de los audios previos para optimizar espacio en Render
            self.voice.limpiar_audio_antiguo()
            
            # El VoicePlugin genera la respuesta de voz con el texto depurado
            self.voice.texto_a_voz(answer, filename=audio_filename)

            return {"text": answer, "audio_file": audio_filename}

        except Exception as e:
            return {"text": f"Error en el núcleo: {str(e)}", "audio_file": None}
