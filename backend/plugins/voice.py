import os
import time
import glob
import asyncio
import edge_tts

class VoicePlugin:
    def __init__(self):
        # Mantenemos la ruta de salida de audio exactamente igual para no romper los buffers de Flask
        self.output_dir = os.getcwd()
        # Sintonizamos la matriz vocal en Español de Venezuela (es-VE) con una voz natural
        self.voice_profile = "es-VE-SebastianNeural" 

    def limpiar_audio_antiguo(self):
        """Escanea el búfer temporal del Mainframe y destruye archivos .mp3 previos."""
        try:
            archivos = glob.glob(os.path.join(self.output_dir, "response_*.mp3"))
            for archivo in archivos:
                # Evitamos borrar un archivo que se esté reproduciendo activamente en ese instante
                if time.time() - os.path.getmtime(archivo) > 10:
                    os.remove(archivo)
        except Exception as e:
            print(f"[NÚCLEO VOCAL]: Error en purga de búfer: {str(e)}")

    async def _generar_audio_edge(self, texto: str, ruta_destino: str):
        """Ejecuta la síntesis asíncrona de Edge-TTS a máxima velocidad."""
        # Limpiamos el formato de comandos ocultos del texto para que Tercero no raye los comandos de automatización
        texto_limpio = re.sub(r'COMMAND_OPEN:\s*(https?:\/\/[^\s]+)', '', texto, flags=re.IGNORECASE).strip()
        if not texto_limpio:
            texto_limpio = "Secuencia ejecutada."

        communicate = edge_tts.Communicate(texto_limpio, self.voice_profile, rate="+5%")
        await communicate.save(ruta_destino)

    def texto_a_voz(self, texto: str, filename: str = "response.mp3"):
        """Método maestro síncrono. Actúa como puente y supervisor de resiliencia vocal."""
        ruta_completa = os.path.join(self.output_dir, filename)
        
        try:
            # Forzamos la ejecución del bucle asíncrono de Edge-TTS de manera síncrona para el core
            asyncio.run(self._generar_audio_edge(texto, ruta_completa))
            print(f"[NÚCLEO VOCAL]: Flujo de audio asíncrono inyectado con éxito en {filename}")
            
        except Exception as e:
            print(f"[ANOMALÍA VOCAL]: Pasarela Edge-TTS interrumpida ({str(e)}). Activando protocolo de voz de contingencia.")
            # CONTINGENCIA PASIVA: Si la API de Microsoft falla, creamos un archivo de audio vacío o mínimo
            # Esto evita que core.py se rompa, permitiendo que el frontend procese el texto de forma normal
            try:
                with open(ruta_completa, "wb") as f:
                    # Un byte de silencio para mantener la respuesta del payload estable
                    f.write(b'\xFF\xF3\x44\xC4\x00\x00\x00\x03\x48\x00\x00\x00\x00\x4C\x41\x4D\x45\x33\x2E\x39\x39\x2E\x35')
            except Exception:
                pass
