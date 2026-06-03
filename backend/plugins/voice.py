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
        Convierte texto a MP3 de forma segura eliminando el formato Markdown.
        Si no se provee filename, genera uno con timestamp.
        """
        try:
            if not filename:
                filename = f"response_{int(time.time())}.mp3"
            
            # 1. Filtro avanzado para remover sintaxis Markdown antes de procesar la voz
            # Quita asteriscos de negritas/itálicas, bloques de código, hashtags de títulos y guiones de listas
            texto_sin_markdown = re.sub(r'\*\*|__|\*|_|`|#+\s|^\s*-\s', '', texto, flags=re.MULTILINE)
            
            # 2. Limpieza final para mantener únicamente caracteres legibles y puntuación fluida
            texto_limpio = re.sub(r'[^\w\s.,!?¡¿]', '', texto_sin_markdown)
            
            # Inicializamos gTTS configurado en español nativo fluido
            tts = gTTS(text=texto_limpio, lang="es", slow=False)
            
            ruta_audio_final = os.path.join(self.audio_dir, filename)
            tts.save(ruta_audio_final)
            
            return filename # Devolvemos solo el nombre base del archivo para el mapeo estático de URLs
            
        except Exception as e:
            print(f"[ERROR TTS]: Falló la conversión de texto a voz: {str(e)}")
            return ""

    def limpiar_audio_antiguo(self):
        """
        Borra audios antiguos de forma segura, protegiendo los archivos emitidos 
        recientemente (últimos 30 segundos) para evitar bloqueos o cortes de streaming en Render.
        """
        try:
            ahora = time.time()
            for f in os.listdir(self.audio_dir):
                file_path = os.path.join(self.audio_dir, f)
                if os.path.isfile(file_path):
                    # Obtenemos la última fecha de modificación del archivo
                    tiempo_modificacion = os.path.getmtime(file_path)
                    # Si el archivo tiene más de 30 segundos de vida, se elimina de forma segura
                    if (ahora - tiempo_modificacion) > 30:
                        try:
                            os.remove(file_path)
                        except PermissionError:
                            # Si el servidor aún lo está sirviendo, ignora temporalmente para no tumbar la app
                            pass
        except Exception as e:
            print(f"[ERROR CLEANUP]: No se pudo realizar la purga de audios: {str(e)}")
