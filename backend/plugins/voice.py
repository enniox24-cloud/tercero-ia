# backend/plugins/voice.py
import os
import speech_recognition as sr
from gtts import gTTS

class VoicePlugin:

    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # Sincronizamos dinámicamente con la raíz del proyecto de forma limpia
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.audio_dir = os.path.join(base_dir, "uploads", "responses")
        os.makedirs(self.audio_dir, exist_ok=True)

    def texto_a_voz(self, texto: str, filename: str = "respuesta.mp3") -> str:
        """
        Convierte una cadena de texto en un archivo de audio MP3 real y devuelve su ruta.
        """
        try:
            # Filtramos marcas extrañas o formatos de código antes de hablar
            texto_limpio = texto.replace("`", "").replace("*", "").strip()
            
            # Inicializamos gTTS configurado en español nativo
            tts = gTTS(text=texto_limpio, lang="es", slow=False)
            
            ruta_audio_final = os.path.join(self.audio_dir, filename)
            tts.save(ruta_audio_final)
            
            return ruta_audio_final
        except Exception as e:
            print(f"[ERROR TTS]: Falló la conversión de texto a voz: {str(e)}")
            return ""

    def escuchar_microfono(self) -> str:
        """
        Activa el micrófono de la computadora de forma local para capturar y transcribir una orden.
        """
        try:
            with sr.Microphone() as source:
                print("[Tercero OS] Escuchando matriz de audio local...")
                # Ajuste automático para mitigar el ruido ambiental de la habitación
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio_capturado = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            print("[Tercero OS] Procesando espectro de voz...")
            # Transcribimos usando el código de lenguaje para Venezuela
            texto_transcrito = self.recognizer.recognize_google(audio_capturado, lang="es-VE")
            print(f"[Usuario dijo]: {texto_transcrito}")
            return texto_transcrito

        except sr.WaitTimeoutError:
            return "[Transmisión de voz cortada por inactividad]"
        except sr.UnknownValueError:
            return "[Audio indescifrable en la matriz local]"
        except Exception as e:
            return f"Error en captura de audio STT: {str(e)}"