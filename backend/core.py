import asyncio
import time
import json
from backend.llm import LLM
from backend.memory import MemoryManager
from backend.plugins.voice import VoicePlugin

class TerceroCore:
    def __init__(self):
        # Inicialización de los motores del sistema
        self.llm = LLM()
        self.memoria = MemoryManager()
        self.voz = VoicePlugin()

    def _decidir_agente(self, message: str) -> str:
        """Selector de agentes inteligente para mejorar la especialización."""
        msg_lower = message.lower()
        if any(keyword in msg_lower for keyword in ["archivo", "pdf", "log", "analiza"]):
            return "AGENTE_ANALISTA"
        elif any(keyword in msg_lower for keyword in ["motor", "falla", "sensor", "voltaje", "p0107"]):
            return "AGENTE_MECANICO"
        return "AGENTE_GENERAL"

    async def procesar_peticion(self, user_id: str, message: str) -> dict:
        """Ciclo principal de pensamiento del Mainframe."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._ejecutar_logica, user_id, message)

    def _ejecutar_logica(self, user_id: str, message: str) -> dict:
        try:
            # 1. Selección de rol operativo
            agente_actual = self._decidir_agente(message)
            
            # 2. Recuperación de memoria asociativa
            contexto = self.memoria.recall(user_id)
            
            # 3. Inferencia de IA basada en el agente seleccionado
            prompt_final = f"Sistema [{agente_actual}]. Contexto: {contexto}. Usuario: {message}"
            respuesta = self.llm.chat(prompt_final)
            
            # 4. Memoria persistente (Aprendizaje)
            self.memoria.guardar(user_id, message, respuesta)
            
            # 5. Sintetización de audio (Voice Engine)
            audio_path = self.voz.texto_a_voz(respuesta)
            
            return {
                "text": respuesta,
                "audio": audio_path,
                "agente_usado": agente_actual,
                "status": "success"
            }
        except Exception as e:
            return {
                "text": f"Error en la matriz neuronal: {str(e)}",
                "audio": None,
                "status": "error"
            }
