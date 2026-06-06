# backend/core.py
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
        
        # Base de datos de memoria unificada
        self.db_path = "tercero_memory.db"
        
        # Calculamos la ruta absoluta de subidas para evitar fallos de montaje en Linux/Render
        BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        self.files_dir = os.path.join(BASE_DIR, "uploads", "files")
        
        # Crear directorio de subidas si no existe para evitar fallos de escritura
        if not os.path.exists(self.files_dir):
            os.makedirs(self.files_dir, exist_ok=True)

    def _recuperar_historial_sqlite(self, user_id: str, limite: int = 15) -> list:
        """Carga el historial físico guardado en la base de datos de manera secuencial."""
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

    def _guardar_mensaje_sqlite(self, user_id: str, role: str, content: str):
        """Escribe de forma persistente cada mensaje en la base de datos para no perder la memoria."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historial_chat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    role TEXT,
                    content TEXT
                )
            ''')
            cursor.execute(
                "INSERT INTO historial_chat (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ALERTA BASE DE DATOS]: No se pudo escribir en SQLite: {str(e)}")

    def chat(self, user_id: str, message: str) -> dict:
        try:
            # 1. Sincronización de memoria e historial persistente
            history = self._recuperar_historial_sqlite(user_id, limite=15)
            memory = self.memory.recall(user_id)

            # Registramos el comando entrante del operador
            self._guardar_mensaje_sqlite(user_id, "user", message)

            # INTERCEPTOR Y ANALIZADOR DE MATRIZ DE ARCHIVOS
            contenido_extraido = ""
            diagnostico_activo = False
            
            match_archivo = re.search(r"El usuario ha cargado el archivo '([^']+)'", message)
            
            if match_archivo:
                nombre_archivo = match_archivo.group(1)
                ruta_completa = os.path.join(self.files_dir, nombre_archivo)
                
                if os.path.exists(ruta_completa):
                    ext = os.path.splitext(nombre_archivo)[1].lower()
                    
                    if ext in ['.txt', '.py', '.js', '.json', '.html', '.css', '.md', '.log']:
                        try:
                            with open(ruta_completa, 'r', encoding='utf-8', errors='ignore') as f:
                                contenido_extraido = f.read(20000) 
                            
                            if ext == '.log' or any(err in contenido_extraido for err in ['Traceback', 'Error', 'Exception', 'FAIL']):
                                diagnostico_activo = True
                        except Exception as e:
                            contenido_extraido = f"[Fallo al leer la matriz de texto: {str(e)}]"
                            
                    elif ext == '.pdf':
                        contenido_extraido = f"[Documento PDF detectado en el Mainframe: '{nombre_archivo}']. Flujo indexado listo."
                    else:
                        contenido_extraido = f"[Archivo multimedia/Imagen detectado en el Mainframe: '{nombre_archivo}']."

            # 2. Construcción de directrices dinámicas de entorno
            system_content = f"Información contextual de tu operador principal: {memory}."
            
            if contenido_extraido:
                system_content += f"\n\n[DATOS EXTRAÍDOS DE LA MATRIZ DE ARCHIVOS]:\n{contenido_extraido}"
                
            if diagnostico_activo:
                system_content += "\n\n[ALERTA DE AGENTE DE DIAGNÓSTICO]: Se ha detectado un volcado de error crítico en las líneas de código del archivo. Analiza el fallo y provee la solución estructural paso a paso."

            system_message = {
                "role": "system",
                "content": system_content
            }

            # Empaquetado final enviado al pool cognitivo
            messages = [system_message] + history + [{"role": "user", "content": message}]
            answer = self.llm.chat(messages)

            # PROCESADOR DE COMANDOS AVANZADO (TOOLS)
            try:
                match = re.search(r"\{.*\}", answer, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if "tool" in parsed:
                        # Ejecución de la rutina del sistema
                        res = run_tool(parsed["tool"], parsed.get("query", ""))
                        
                        # Inyección del resultado manteniendo el hilo de conversación intacto
                        messages.append({"role": "assistant", "content": answer})
                        messages.append({
                            "role": "system", 
                            "content": f"[RESULTADO DE HERRAMIENTA {parsed['tool'].upper()}]: {res}. Responde al operador interpretando este resultado técnico."
                        })
                        answer = self.llm.chat(messages)
            except Exception as e:
                print(f"[SISTEMA TOOLS]: Fallo en ejecución secuencial: {str(e)}")

            # Registramos de forma permanente la respuesta final de Tercero
            self._guardar_mensaje_sqlite(user_id, "assistant", answer)

            # 3. Flujo del motor de voz pasiva
            audio_filename = f"response_{int(time.time())}.mp3"
            self.voice.limpiar_audio_antiguo()
            self.voice.texto_a_voz(answer, filename=audio_filename)

            return {"text": answer, "audio_file": audio_filename}

        except Exception as e:
            return {"text": f"Error en el núcleo de Tercero: {str(e)}", "audio_file": None}

    def procesar_archivo(self, user_id: str, ruta_archivo: str) -> dict:
        """Procesa de forma segura cualquier inyección de archivos del HUD sin usar modelos obsoletos."""
        try:
            nombre_archivo = os.path.basename(ruta_archivo)
            ext = os.path.splitext(nombre_archivo)[1].lower()
            contenido = ""
            
            if ext in ['.txt', '.py', '.js', '.json', '.html', '.css', '.md', '.log']:
                with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
                    contenido = f.read(15000)
                prompt = f"El usuario ha inyectado el archivo '{nombre_archivo}'. Contenido:\n\n{contenido}\n\nAnaliza la estructura de este archivo y confirma su correcto procesamiento."
            elif ext == '.pdf':
                prompt = f"El usuario ha cargado el documento PDF '{nombre_archivo}'. Confirma la indexación del archivo en el sistema."
            else:
                prompt = f"El usuario ha inyectado el archivo multimedia o imagen '{nombre_archivo}' al sistema. Confirma la recepción del recurso de manera asertiva."
            
            # Procesamos usando la matriz limpia de llm.py
            respuesta_texto = self.llm.chat([{"role": "user", "content": prompt}])
            
            # Persistencia en base de datos de telemetría
            self._guardar_mensaje_sqlite(user_id, "user", f"[Inyección de Medio]: {nombre_archivo}")
            self._guardar_mensaje_sqlite(user_id, "assistant", respuesta_texto)
            
            # Generación de voz
            audio_filename = f"response_{int(time.time())}.mp3"
            self.voice.limpiar_audio_antiguo()
            self.voice.texto_a_voz(respuesta_texto, filename=audio_filename)
            
            return {"text": respuesta_texto, "audio_file": audio_filename}
        except Exception as e:
            return {"text": f"Fallo estructural en procesamiento de archivo: {str(e)}", "audio_file": None}
