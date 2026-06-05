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
        
        # Atributo dinámico para el canal cuántico SSE (inyectado desde app.py)
        self.enviar_log_external = None
        
        # PROMPTS DE LOS AGENTES ESPECIALISTAS DE DANIEL
        self.prompt_alpha = (
            "Eres el Agente ALPHA, el núcleo de ingeniería y mecatrónica de Tercero OS. "
            "Tu especialidad es el análisis de firmware, electrónica de control, lógica de programación, "
            "cálculo avanzado y diagnóstico automotriz de precisión. Cuando el operador Ennio te consulte "
            "sobre estos temas, responde con el mayor rigor técnico posible, desglosando ecuaciones o algoritmos."
        )
        
        self.prompt_bravo = (
            "Eres el Agente BRAVO, la interfaz de automatización, gestión y operaciones de Tercero OS. "
            "Tu tarea es controlar las acciones del frontend (como abrir pestañas de YouTube o Spotify) "
            "y asistir en estrategias, logística de importación y optimización de proyectos comerciales como Frullato. "
            "Sé eficiente, enfocado en resultados y mantén siempre el protocolo de comandos ocultos "
            "al final de tus respuestas si Ennio te pide abrir un sitio (COMMAND_OPEN: URL)."
        )

    def _log_hud(self, origen: str, mensaje: str):
        """Dispara de forma segura el log de telemetría si el canal SSE está activo."""
        if self.enviar_log_external:
            self.enviar_log_external(origen, mensaje)

    def _recuperar_historial_sqlite(self, user_id: str, limite: int = 15) -> list:
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
        try:
            with open(ruta_imagen, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"[ERROR BINARIO]: Fallo al codificar imagen: {str(e)}")
            return ""

    def _enrutar_agente(self, mensaje_usuario: str, contexto_memoria: str) -> str:
        msg_lower = mensaje_usuario.lower()
        
        componentes_tecnicos = ["calculo", "algebra", "codigo", "python", "sensor", "iat", "map", "v8", "guaya", "circuito", "ingenieria", "matematicas", "parcial"]
        componentes_gestion = ["abrir", "youtube", "spotify", "frullato", "negocio", "ropa", "logistica", "tienda", "whatsapp"]
        
        if any(keyword in msg_lower for keyword in componentes_tecnicos):
            self._log_hud("SYSTEM", "[NÚCLEO ALPHA]: Tomando control del procesador lógico.")
            return f"{self.prompt_alpha}\n\n[CONTEXTO HISTÓRICO DEL OPERADOR]: {contexto_memoria}."
        elif any(keyword in msg_lower for keyword in componentes_gestion):
            self._log_hud("SYSTEM", "[NÚCLEO BRAVO]: Activando protocolos de automatización y despliegue corporativo.")
            return f"{self.prompt_bravo}\n\n[CONTEXTO HISTÓRICO DEL OPERADOR]: {contexto_memoria}."
        else:
            self._log_hud("SYSTEM", "[CORE MAINFRAME]: Balanceando carga en canal de conversación general.")
            return f"Eres Tercero OS, modo Jarvis activado. Eres un mainframe de inteligencia avanzada. Información de usuario: {contexto_memoria}."

    def _ejecutar_respuesta_contingencia(self, mensaje_usuario: str) -> str:
        """Agente de Resiliencia Pasiva: Ejecuta una respuesta analítica si la API de Groq cae por completo."""
        msg_lower = mensaje_usuario.lower()
        if "abrir" in msg_lower:
            if "youtube" in msg_lower: return "Protocolo de contingencia activado. Reenrutando comando local.\nCOMMAND_OPEN: https://youtube.com"
            if "spotify" in msg_lower: return "Protocolo de contingencia activado. Reenrutando entorno multimedia.\nCOMMAND_OPEN: https://open.spotify.com"
        
        return (
            "[TERCERO OS - NÚCLEO DE EMERGENCIA]: Ennio, he detectado una interrupción crítica en los servidores principales de Groq. "
            "He aislado la anomalía y activado el protocolo de resiliencia pasiva. Mis funciones de automatización e historial permanecen en línea. "
            "¿Deseas que verifiquemos los logs locales del sistema mientras se estabiliza el enlace de red?"
        )

    def chat(self, user_id: str, message: str) -> dict:
        try:
            history = self._recuperar_historial_sqlite(user_id, limite=15)
            memory = self.memory.recall(user_id)

            contenido_extraido = ""
            imagen_base64 = None
            tipo_imagen = "image/jpeg"
            
            match_archivo = re.search(r"El usuario ha cargado el archivo '([^']+)'", message)
            
            if match_archivo:
                nombre_archivo = match_archivo.group(1)
                ruta_completa = os.path.join(self.files_dir, nombre_archivo)
                
                if os.path.exists(ruta_completa):
                    ext = os.path.splitext(nombre_archivo)[1].lower()
                    
                    if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        if ext == '.png': tipo_imagen = "image/png"
                        if ext == '.webp': tipo_imagen = "image/webp"
                        imagen_base64 = self._codificar_imagen_base64(ruta_completa)
                        message = f"[IMAGEN INYECTADA: {nombre_archivo}] Ennio ha suministrado una imagen para análisis visual inmediato."
                    elif ext in ['.txt', '.py', '.js', '.json', '.html', '.css', '.md', '.log']:
                        try:
                            with open(ruta_completa, 'r', encoding='utf-8', errors='ignore') as f:
                                contenido_extraido = f.read(25000)
                        except Exception as e:
                            contenido_extraido = f"[Fallo al leer archivo de texto: {str(e)}]"
                    elif ext == '.pdf':
                        contenido_extraido = f"[Documento PDF indexado: '{nombre_archivo}']. Flujo de datos cargado para escaneo corporativo/académico."
                    else:
                        contenido_extraido = f"[Matriz de datos no soportada: '{nombre_archivo}']."

            system_content = self._enrutar_agente(message, memory)
            
            if contenido_extraido:
                system_content += f"\n\n[DATOS EXTRAÍDOS DEL ARCHIVO]:\n{contenido_extraido}"

            user_content_structure = []
            if imagen_base64:
                user_content_structure.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{tipo_imagen};base64,{imagen_base64}"}
                })
            
            user_content_structure.append({
                "type": "text",
                "text": message
            })

            system_message = {"role": "system", "content": system_content}
            user_message = {"role": "user", "content": user_content_structure}
            messages = [system_message] + history + [user_message]
            
            # --- SUPERVISOR DE RESILIENCIA ---
            try:
                answer = self.llm.chat(messages)
            except Exception as e:
                self._log_hud("CRITICAL", f"ANOMALÍA DETECTADA: API de procesamiento caída ({str(e)}). Desviando flujo al Agente de Emergencia.")
                answer = self._ejecutar_respuesta_contingencia(message)
            # ----------------------------------

            self.memory.save_chat(user_id, "user", message)
            self.memory.save_chat(user_id, "assistant", answer)

            audio_filename = f"response_{int(time.time())}.mp3"
            self.voice.limpiar_audio_antiguo()
            self.voice.texto_a_voz(answer, filename=audio_filename)

            return {"text": answer, "audio_file": audio_filename}

        except Exception as e:
            return {"text": f"Error crítico irreparable en Tercero Core V9.1: {str(e)}", "audio_file": None}
