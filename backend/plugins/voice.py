import os
import time
from gtts import gTTS

class VoicePlugin:

    def __init__(self):
        # Usamos una ruta absoluta relativa al directorio actual
        # Esto asegura que siempre se encuentre la carpeta 'uploads/responses'
        self.audio_dir = os.path.join(os.getcwd(), "uploads", "responses")
        os.makedirs(self.audio_dir, exist_ok=True)

    def texto_a_voz(self, texto: str, filename: str = None) -> str:
        """
        Convierte texto a MP3. Si no se provee filename, genera uno con timestamp.
        """
        try:
            if not filename:
                filename = f"response_{int(time.time())}.mp3"
            
            # Limpieza para voz más natural (evita que diga caracteres raros)
            texto_limpio = re.sub(r'[^\w\s.,!?¡¿]', '', texto)
            
            # gTTS es excelente para español neutral
            tts = gTTS(text=texto_limpio, lang="es", slow=False)
            
            ruta_audio_final = os.path.join(self.audio_dir, filename)
            tts.save(ruta_audio_final)
            
            return filename # Devolvemos solo el nombre del archivo
            
        except Exception as e:
            print(f"[ERROR TTS]: {str(e)}")
            return ""

    def limpiar_audio_antiguo(self):
        """Borra audios antiguos para que Render no se quede sin espacio."""
        for f in os.listdir(self.audio_dir):
            file_path = os.path.join(self.audio_dir, f)
            if os.path.isfile(file_path):
                os.remove(file_path)
