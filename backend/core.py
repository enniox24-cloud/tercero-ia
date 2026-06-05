import json
import time
import re
import os
import sqlite3
import base64
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

    def _codificar_imagen_base64(self, ruta_imagen: str) -> str:
        """Convierte un archivo de imagen a una cadena Base64 legible para el modelo de visión."""
        try:
            with open(ruta_imagen, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"[ERROR BINARIO]: Fallo al codificar imagen: {str(e)}")
            return ""

    def chat(self, user_id: str, message: str) -> dict:
        try:
            # 1. Recuperación del historial y contexto de Ennio
            history = self._recuperar_historial_sqlite(user_id, limite=15)
            memory = self.memory.recall(user_id)

            # ESTRUCTURACIÓN DE MENSAJE MULTIMODAL V8
            contenido_extraido = ""
            imagen_base64 = None
            tipo_imagen = "image/jpeg"
            
            # Interceptamos si el mensaje del sistema indica una inyección de archivo
            match_archivo = re.search(r"El usuario ha cargado el archivo '([^']+)'", message)
            
            if match_archivo:
                nombre_archivo = match_archivo.group(1)
                ruta_completa = os.path.join(self.files_dir, nombre_archivo)
                
                if os.path.exists(ruta_completa):
                    ext = os.path.splitext(nombre_archivo)[1].lower()
                    
                    # PROCESAMIENTO DE IMÁGENES (VISIÓN ACTIVA)
                    if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        if ext == '.png': tipo_imagen = "image/png"
                        if ext == '.webp': tipo_imagen = "image/webp"
                        
                        imagen_base64 = self._codificar_imagen_base64(ruta_completa)
                        message = f"[IMAGEN INYECTADA: {nombre_archivo}] Ennio ha suministrado una imagen para análisis visual inmediato."
                    
                    # PROCESAMIENTO DE ARCHIVOS DE TEXTO Y CÓDIGO
                    elif ext in ['.txt', '.py', '.js', '.json', '.html', '.css', '.md', '.log']:
                        try:
                            with open(ruta_completa, 'r', encoding='utf-8', errors='ignore') as f:
                                contenido_extraido = f.read(25000)
                        except Exception as e:
                            contenido_extraido = f"[Fallo al leer archivo de texto: {str(e)}]"
                            
                    elif ext == '.pdf':
                        contenido_extraido = f"[Documento PDF indexado: '{nombre_archivo}']. Flujo de datos cargado para escaneo de texto corporativo/académico."
                    else:
                        contenido_extraido = f"[Matriz de datos no soportada: '{nombre_archivo}']."

            # 2. Configuración del prompt del sistema de Tercero
            system_content = f"Eres Tercero OS, un mainframe de inteligencia avanzada. Información de usuario: {memory}. {self.llm.system_prompt}."
            
            if contenido_extraido:
                system_content += f"\n\n[DATOS EXTRAÍDOS DEL ARCHIVO]:\n{contenido_extraido}"

            # Construimos la estructura de mensajes compatible con Llama Vision
            user_content_structure = []
            
            # Si hay una imagen codificada, inyectamos el bloque multimedia requerido por Groq
            if imagen_base64:
                user_content_structure.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{tipo_imagen};base64,{imagen_base64}"
                    }
                })
            
            # Agregamos obligatoriamente el prompt de texto del operador
            user_content_structure.append({
                "type": "text",
                "text": message
            })

            # Empaquetamos el hilo completo
            system_message = {"role": "system", "content": system_content}
            user_message = {"role": "user", "content": user_content_structure}
            
            messages = [system_message] + history + [user_message]
            
            # 3. Transmisión al LLM Multimodal
            answer = self.llm.chat(messages)

            # 4. Generación vocal automatizada
            audio_filename = f"response_{int(time.time())}.mp3"
            self.voice.limpiar_audio_antiguo()
            self.voice.texto_a_voz(answer, filename=audio_filename)

            return {"text": answer, "audio_file": audio_filename}

        except Exception as e:
            return {"text": f"Error crítico en Tercero Core V8: {str(e)}", "audio_file": None}
