import asyncio
from backend.llm import LLM
from backend.memory import MemoryManager
from backend.plugins.voice import VoicePlugin

class TerceroCore:
    def __init__(self):
        self.llm = LLM()
        self.memoria = MemoryManager()
        self.voz = VoicePlugin()

    async def procesar_peticion(self, user_id, message):
        loop = asyncio.get_event_loop()
        # Procesamos todo en un hilo secundario para no congelar el servidor
        return await loop.run_in_executor(None, self._ejecutar_logica, user_id, message)

    def _ejecutar_logica(self, user_id, message):
        try:
            # 1. Recuperación asociativa
            contexto = self.memoria.recall(user_id)
            
            # 2. Inferencia (IA)
            respuesta = self.llm.chat(f"Contexto: {contexto}. Mensaje: {message}")
            
            # 3. Almacenamiento evolutivo
            self.memoria.guardar(user_id, message, respuesta)
            
            # 4. Sintetización vocal
            audio = self.voz.texto_a_voz(respuesta)
            
            return {"text": respuesta, "audio": audio, "status": "active"}
        except Exception as e:
            return {"text": f"Error en núcleo: {str(e)}", "audio": None}
