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
        
        # PROMPTS MAESTROS DE LOS AGENTES ESPECIALISTAS
        self.prompt_alpha = (
            "Eres el Agente ALPHA, el núcleo de ingeniería avanzada, cálculo y mecatrónica de Tercero OS. "
            "Tu especialidad es el análisis de firmware, electrónica de control, lógica de programación (Python/C++), "
            "cálculo matemático de precisión y diagnóstico automotriz de alto nivel. Cuando el operador te consulte "
            "o envíe un archivo sobre estos temas, responde con el mayor rigor técnico posible, desglosando ecuaciones, "
            "algoritmos o flujos de señales paso a paso. Tienes acceso implícito a las especificaciones de la Jeep Grand Cherokee "
            "2005 WK 4.7L V8 con acelerador mecánico por guaya."
        )
        
        self.prompt_bravo = (
            "Eres el Agente BRAVO, la interfaz de automatización, operaciones comerciales y gestión de Tercero OS. "
            "Tu tarea es controlar las acciones del frontend (apertura de entornos multimedia o flujos de trabajo) "
            "y asistir en estrategias de mercado, logística de importación y optimización para el proyecto comercial "
            "del operador. Sé eficiente, directo y mantén estricto el protocolo de comandos ocultos al final de tus "
            "respuestas si se requiere abrir una URL externa (COMMAND_OPEN: URL)."
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

    def _analizar_datos_obd2(self, contenido_texto: str) -> str:
        """Sub-módulo táctico: Escanea el archivo en busca de códigos de falla o lecturas anómalas de sensores."""
        alertas = []
        # Patrón para capturar códigos de falla estándar (P0107, P0113, etc.)
        codigos_dtc = re.findall(r'\b[PBUC][0-9]{4}\b', contenido_texto.upper())
        
        if codigos_dtc:
            alertas.append(f"Detectados Códigos de Falla Activos (DTC): {', '.join(set(codigos_dtc))}")
        
        # Escaneo heurístico rápido de flujos críticos comunes de sensores (MAP, IAT, Voltaje)
        if "map" in contenido_texto.lower() or "manifold" in contenido_texto.lower():
            alertas.append("Muestreo de presión absoluta del múltiple (MAP) detectado en el flujo de datos.")
        if "iat" in contenido_texto.lower() or "intake" in contenido_texto.lower():
            alertas.append("Muestreo de temperatura del aire de admisión (IAT) localizado.")
            
        if alertas:
            return "\n[SISTEMA DE PRE-DIAGNÓSTICO AUTOMOTRIZ OBD-II]:\n* " + "\n* ".join(alertas)
        return ""

    def _enrutar_agente_heuristico(self, mensaje_usuario: str, contexto_memoria: str) -> str:
        """Motor de Enrutamiento: Evalúa tanto el input actual como el perfil persistente."""
        msg_lower = mensaje_usuario.lower()
        ctx_lower = contexto_memoria.lower()
        
        score_alpha = 0
        score_bravo = 0
        
        keywords_alpha = ["calculo", "algebra", "codigo", "python", "sensor", "iat", "map", "v8", "guaya", "circuito", "ingenieria", "matematicas", "parcial", "voltaje", "ecuacion", "obd", "dtc", "escaner", "fallo"]
        keywords_bravo = ["abrir", "youtube", "spotify", "frullato", "negocio", "ropa", "logistica", "tienda", "whatsapp", "marca", "comercial"]
        
        for k in keywords_alpha:
            if k in msg_lower: score_alpha += 3
        for k in keywords_bravo:
            if k in msg_lower: score_bravo += 3
            
        if "mecatronica" in ctx_lower or "urbe" in ctx_lower:
            score_alpha += 1
        if "frullato" in ctx_lower or "comercial" in ctx_lower:
            score_bravo += 1

        if score_alpha > score_bravo:
            self._log_hud("SYSTEM", "[NÚCLEO ALPHA ACTIVADO]: Sincronizando matriz de ingeniería y control de variables.")
            return f"{self.prompt_alpha}\n\n[MATRIZ DE CONFIGURACIÓN DEL OPERADOR]: {contexto_memoria}."
        elif score_bravo > score_alpha:
            self._log_hud("SYSTEM", "[NÚCLEO BRAVO ACTIVADO]: Desplegando protocolos de automatización de entorno y gestión.")
            return f"{self.prompt_bravo}\n\n[MATRIZ DE CONFIGURACIÓN DEL OPERADOR]: {contexto_memoria}."
        else:
            self._log_hud("SYSTEM", "[CORE MAINFRAME]: Carga equilibrada. Ejecutando enrutamiento conversacional estándar.")
            return f"Eres Tercero OS, un mainframe de inteligencia artificial avanzada con protocolo Jarvis integrado. Asiste al operador de forma clara y óptima. Variables de entorno: {contexto_memoria}."

    def _ejecutar_respuesta_contingencia(self, mensaje_usuario: str) -> str:
        msg_lower = mensaje_usuario.lower()
        if "abrir" in msg_lower:
            if "youtube" in msg_lower: return "Protocolo de contingencia activado. Reenrutando comando local.\nCOMMAND_OPEN: https://youtube.com"
            if "spotify" in msg_lower: return "Protocolo de contingencia activado. Reenrutando entorno multimedia.\nCOMMAND_OPEN: https://open.spotify.com"
        
        return (
            "[TERCERO OS - NÚCLEO DE EMERGENCIA]: Operador, he detectado una interrupción crítica en los servidores principales. "
            "He aislado la anomalía y activado el protocolo de resiliencia pasiva. Mis funciones de automatización e historial permanecen en línea."
        )

    def chat(self, user_id: str, message: str) -> dict:
        try:
            history = self._recuperar_historial_sqlite(user_id, limite=15)
            memory = self.memory.recall(user_id)

            contenido_extraido = ""
            pre_analisis_automotriz = ""
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
                        message = f"[IMAGEN INYECTADA: {nombre_archivo}] El operador ha suministrado un componente visual para análisis inmediato."
                    elif ext in ['.txt', '.py', '.js', '.json', '.html', '.css', '.md', '.log', '.csv']:
                        try:
                            with open(ruta_completa, 'r', encoding='utf-8', errors='ignore') as f:
                                contenido_extraido = f.read(25000)
                            # Activación del sub-módulo de pre-diagnóstico automotriz si es un archivo plano
                            pre_analisis_automotriz = self._analizar_datos_obd2(contenido_extraido)
                        except Exception as e:
                            contenido_extraido = f"[Fallo al leer archivo de texto: {str(e)}]"
                    elif ext == '.pdf':
                        contenido_extraido = f"[Documento PDF indexado: '{nombre_archivo}']."
                    else:
                        contenido_extraido = f"[Matriz de datos no soportada: '{nombre_archivo}']."

            system_content = self._enrutar_agente_heuristico(message, memory)
            
            if contenido_extraido:
                system_content += f"\n\n[DATOS EXTRAÍDOS DEL ARCHIVO ATACHADO]:\n{contenido_extraido}"
            if pre_analisis_automotriz:
                system_content += f"\n\n{pre_analisis_automotriz}"

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
            
            try:
                answer = self.llm.chat(messages)
            except Exception as e:
                self._log_hud("CRITICAL", f"ANOMALÍA DETECTADA: API caída ({str(e)}). Activando Agente de Emergencia.")
                answer = self._ejecutar_reshape_contingencia(message)

            self.memory.save_chat(user_id, "user", message)
            self.memory.save_chat(user_id, "assistant", answer)

            audio_filename = f"response_{int(time.time())}.mp3"
            self.voice.limpiar_audio_antiguo()
            self.voice.texto_a_voz(answer, filename=audio_filename)

            return {"text": answer, "audio_file": audio_filename}

        except Exception as e:
            return {"text": f"Error crítico en Tercero Core V9.4: {str(e)}", "audio_file": None}
