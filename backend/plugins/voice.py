import os
import time
import re
from gtts import gTTS

class VoicePlugin:

    def __init__(self):
        # Usamos una ruta absoluta relativa al directorio de ejecución actual
        # Esto asegura que siempre se encuentre la carpeta 'uploads/responses' en Render
        self.audio_dir = os.path.join(os.getcwd(), "uploads", "responses")
        os.makedirs(self.audio_dir, exist_ok=True)

    def texto_a_voz(self, texto: str, filename: str = None) -> str:
        """
        Convierte texto a MP3 de forma segura. Si no se provee filename, genera uno con timestamp.
        """
        try:
            if not filename:
                filename = f"response_{int(time.time())}.mp3"
            
            # Limpieza para voz más natural usando la librería 're' correctamente importada
            texto_limpio = re.sub(r'[^\w\s.,!?¡¿]', '', texto)
            
            # Inicializamos gTTS configurado en español nativo fluido
            tts = gTTS(text=texto_limpio, lang="es", slow=False)
            
            ruta_audio_final = os.path.join(self.audio_dir, filename)
            tts.save(ruta_audio_final)
            
            return filename # Devolvemos solo el nombre base del archivo para el mapeo estático de URLs
            
        except Exception as e:
            print(f"[ERROR TTS]: Falló la conversión de texto a voz: {str(e)}")
            return ""

    def limpiar_audio_antiguo(self):
        """Borra audios antiguos para evitar que el almacenamiento efímero de Render se sature."""
        try:
            for f in os.listdir(self.audio_dir):
                file_path = os.path.join(self.audio_dir, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"[ERROR CLEANUP]: No se pudo realizar la purga de audios: {str(e)}")
