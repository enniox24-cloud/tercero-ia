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
        
        # Ruta unificada de base de datos
        self.db_path = "tercero_memory.db"
        
        # Determinamos la ruta absoluta para evitar fallos de ubicación en Render
        BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        self.files_dir = os.path.join(BASE_DIR, "uploads", "files")

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

    def _guardar_mensaje_sqlite(self, user_id: str, role: str, content: str):
        """SOLUCIÓN: Registra de forma persistente cada interacción en la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Creamos la tabla de respaldo si por alguna razón no existe
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
            print(f"[ERROR PERSISTENCIA]: No se pudo escribir en SQLite: {str(e)}")

    def chat(self, user_id: str, message: str) -> dict:
        try:
            # 1. Recuperación del historial real persistente desde SQLite y memoria secundaria
            history = self._recuperar_historial_sqlite(user_id, limite=15)
            memory = self.memory.recall(user_id)

            # Guardamos el mensaje entrante del usuario de inmediato
            self._guardar_mensaje_sqlite(user_id, "user", message)

            # INTERCEPTOR Y EXTRACTOR DE MATRIZ DE ARCHIVOS AVANZADO
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
                                contenido_extraido = f.read(20000) # Expandido a 20k caracteres
                            
                            # Alertas de diagnóstico si detectamos anomalías o excepciones
                            if ext == '.log' or any(err in contenido_extraido for err in ['Traceback', 'Error', 'Exception', 'FAIL']):
                                diagnostico_activo = True
                        except Exception as e:
                            contenido_extraido = f"[Fallo al leer la matriz de texto: {str(e)}]"
                            
                    elif ext == '.pdf':
                        contenido_extraido = f"[Documento PDF detectado en el Mainframe: '{nombre_archivo}'. Flujo de datos indexado listo para escaneo]."
                    else:
                        contenido_extraido = f"[Archivo binario/Imagen detectado en el Mainframe: '{nombre_archivo}']."

            # 2. Configuración de directrices del sistema de Tercero OS (Limpiando duplicaciones)
            system_content = f"Información de contexto de tu operador principal (Ennio): {memory}."
            
            if contenido_extraido:
                system_content += f"\n\n[DATOS EXTRAÍDOS DE LA MATRIZ DE ARCHIVOS]:\n{contenido_extraido}"
                
            if diagnostico_activo:
                system_content += "\n\n[ALERTA DE AGENTE]: Se ha detectado un volcado de error o log crítico de consola en el archivo. Analiza las líneas de código afectadas, localiza el fallo exacto en el backend/frontend y provee una solución estructurada paso a paso."

            system_message = {
                "role": "system",
                "content": system_content
            }

            # Compilación final del paquete de mensajes
            messages = [system_message] + history + [{"role": "user", "content": message}]
            answer = self.llm.chat(messages)

            # PROCESADOR DE COMANDOS (TOOLS) REFORZADO CON RETENCIÓN DE MEMORIA
            try:
                match = re.search(r"\{.*\}", answer, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if "tool" in parsed:
                        res = run_tool(parsed["tool"], parsed.get("query", ""))
                        
                        # SOLUCIÓN: Añadimos la respuesta intermedia y el output de la herramienta al hilo existente
                        messages.append({"role": "assistant", "content": answer})
                        messages.append({
                            "role": "system", 
                            "content": f"[RESULTADO DE LA HERRAMIENTA {parsed['tool'].upper()}]: {res}. Interpreta este resultado técnico y respóndele a Ennio de forma asertiva."
                        })
                        # Re-evaluación con el contexto completo intacto
                        answer = self.llm.chat(messages)
            except Exception as e:
                print(f"[ANOMALÍA TOOL]: Error procesando comandos: {str(e)}")

            # Guardamos de forma persistente la respuesta final generada por Tercero
            self._guardar_mensaje_sqlite(user_id, "assistant", answer)

            # Generamos el archivo de audio de salida de forma limpia
            audio_filename = f"response_{int(time.time())}.mp3"
            
            # Limpieza automática de búfer para optimizar almacenamiento en Render
            self.voice.limpiar_audio_antiguo()
            
            # Conversión vocal a través del VoicePlugin
            self.voice.texto_a_voz(answer, filename=audio_filename)

            return {"text": answer, "audio_file": audio_filename}

        except Exception as e:
            return {"text": f"Error en el núcleo de Tercero: {str(e)}", "audio_file": None}
