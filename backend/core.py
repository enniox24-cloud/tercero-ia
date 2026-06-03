import json
import time
import re
import os
import sqlite3
from backend.llm import LLM
from backend.memory import MemoryManager
from backend.tools import run_tool
from backend.plugins.voice import VoicePlugin

class TerceroCore:
    def __init__(self):
        self.llm = LLM()
        self.memory = MemoryManager()
        self.voice = VoicePlugin()
        # Ruta de la base de datos de memoria unificada
        self.db_path = "tercero_memory.db"
        # Definimos la ruta de la matriz de archivos para poder escanearlos
        self.files_dir = os.path.join(os.getcwd(), "uploads", "files")

    def _recuperar_historial_sqlite(self, user_id: str, limite: int = 15) -> list:
        """Carga de forma segura el historial físico guardado en la base de datos."""
        try:
            if not os.path.exists(self.db_path):
                return []
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content FROM historial_chat WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limite)
            )
            filas = cursor.fetchall()
            conn.close()
            return [{"role": f[0], "content": f[1]} for f in reversed(filas)]
        except Exception:
            return []

    def chat(self, user_id: str, message: str) -> dict:
        try:
            # 1. Recuperación cuántica del historial persistente desde SQLite
            # Solicitamos 16 registros para compensar la inserción previa en main.py
            raw_history = self._recuperar_historial_sqlite(user_id, limite=16)
            
            # CONTROL DE TOKENS: Si el último mensaje guardado coincide con el actual, 
            # lo removemos del historial para evitar la duplicación de contexto en el LLM.
            if raw_history and raw_history[-1]["role"] == "user" and raw_history[-1]["content"] == message:
                history = raw_history[:-1]
            else:
                history = raw_history[-15:] # Mantener una ventana máxima estable de 15 mensajes

            memory = self.memory.recall(user_id)

            # INTERCEPTOR Y EXTRACTOR DE MATRIZ DE ARCHIVOS AVANZADO (MÓDULO DE AGENTE)
            contenido_extraido = ""
            diagnostico_activo = False
            
            match_archivo = re.search(r"El usuario ha cargado el archivo '([^']+)'", message)
            
            if match_archivo:
                nombre_archivo = match_archivo.group(1)
                ruta_completa = os.path.join(self.files_dir, nombre_archivo)
                
                if os.path.exists(ruta_completa):
                    ext = os.path.splitext(nombre_archivo)[1].lower()
                    
                    # Soporte extendido para logs, scripts y configuraciones de servidores
                    if ext in ['.txt', '.py', '.js', '.json', '.html', '.css', '.md', '.log']:
                        try:
                            with open(ruta_completa, 'r', encoding='utf-8', errors='ignore') as f:
                                contenido_extraido = f.read(20000) # Expandido a 20k caracteres para reportes largos
                            
                            # Si detectamos un archivo .log o rastros de errores, encendemos las alertas de diagnóstico
                            if ext == '.log' or any(err in contenido_extraido for err in ['Traceback', 'Error', 'Exception', 'FAIL']):
                                diagnostico_activo = True
                        except Exception as e:
                            contenido_extraido = f"[Fallo al leer la matriz de texto: {str(e)}]"
                            
                    elif ext == '.pdf':
                        contenido_extraido = f"[Documento PDF detectado en el Mainframe: '{nombre_archivo}'. Flujo de datos indexado listo para escaneo]."
                    else:
                        contenido_extraido = f"[Archivo binario/Imagen detectado en el Mainframe: '{nombre_archivo}']."

            # 2. Configuración de directrices del sistema de Tercero OS
            system_content = f"Eres Tercero OS, un mainframe de inteligencia avanzada. Información de usuario: {memory}. {self.llm.system_prompt}."
            
            if contenido_extraido:
                system_content += f"\n\n[DATOS EXTRAÍDOS DE LA MATRIZ DE ARCHIVOS]:\n{contenido_extraido}"
                
            if diagnostico_activo:
                system_content += "\n\n[ALERTA DE AGENTE]: Se ha detectado un volcado de error o log crítico de consola en el archivo. Analiza las líneas de código afectadas, localiza el fallo exacto en el backend/frontend y provee una solución estructurada paso a paso."

            system_message = {
                "role": "system",
                "content": system_content
            }

            # Compilación final del paquete de mensajes libre de duplicaciones
            messages = [system_message] + history + [{"role": "user", "content": message}]
            answer = self.llm.chat(messages)

            # PROCESADOR DE COMANDOS (TOOLS)
            try:
                match = re.search(r"\{.*\}", answer, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if "tool" in parsed:
                        res = run_tool(parsed["tool"], parsed.get("query", ""))
                        answer = self.llm.chat([
                            {"role": "system", "content": f"Resultado de herramienta: {res}. Explícalo al usuario de manera asertiva."},
                            {"role": "user", "content": message}
                        ])
            except Exception:
                pass

            # Generamos el archivo de audio de salida de forma limpia
            audio_filename = f"response_{int(time.time())}.mp3"
            
            # Limpieza automática de búfer para optimizar almacenamiento en Render
            self.voice.limpiar_audio_antiguo()
            
            # Conversión vocal a través del VoicePlugin
            self.voice.texto_a_voz(answer, filename=audio_filename)

            return {"text": answer, "audio_file": audio_filename}

        except Exception as e:
            return {"text": f"Error en el núcleo de Tercero: {str(e)}", "audio_file": None}
