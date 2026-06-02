# backend/agente_ambiental.py
import os
import time
import requests
import speech_recognition as sr
import pygame

# Configuración base del sistema operativo
URL_STATUS = "http://localhost:8000/status"
URL_AUDIO_ENDPOINT = "http://localhost:8000/chat-audio"
URL_STATIC_AUDIO = "http://localhost:8000/static/audio/"
WAKE_WORD = "tercero"

# Inicializamos el reproductor de audio local
pygame.mixer.init()

def reproducir_respuesta_local(url_audio):
    """Descarga el audio generado por el servidor y lo reproduce en las cornetas."""
    try:
        response = requests.get(url_audio, stream=True)
        if response.status_code == 200:
            temp_file = "temp_response.mp3"
            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            
            # Reproducción nativa en Windows
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
            pygame.mixer.music.unload()
            try:
                os.remove(temp_file)
            except Exception:
                pass # Evita bloqueos si el sistema operativo tarda en liberar el archivo
    except Exception as e:
        print(f"[Sistema de Audio Local] Error al reproducir: {e}")

def verificar_servidor():
    """Verifica si el mainframe de FastAPI está encendido antes de escuchar."""
    try:
        r = requests.get(URL_STATUS, timeout=2)
        return r.status_code == 200
    except:
        return False

def iniciar_escucha_ambiental():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    # Ajustes de calibración para el ruido de fondo de la habitación
    with microphone as source:
        print("\n[Tercero OS] Calibrando espectro acústico ambiental... Silencio por favor.")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print("[Tercero OS] Calibración completa. Matriz en espera estable...")
        print(f"-> Di la palabra clave de activación: '{WAKE_WORD.upper()}' seguido de tu orden.\n")

    while True:
        try:
            if not verificar_servidor():
                print("[ADVERTENCIA] Servidor local offline... Reintentando conexión en 5s.")
                time.sleep(5)
                continue

            with microphone as source:
                # Escucha constante con un timeout ligero para no congelar el procesador
                audio = recognizer.listen(source, phrase_time_limit=8)

            print("[Procesando espectro de voz local...]")
            
            # Transcripción rápida local para capturar la palabra clave
            try:
                # CORRECCIÓN DE MATRIZ: Se usa 'language' en vez de 'lang' para evitar la anomalía legacy
                texto_capturado = recognizer.recognize_google(audio, language="es-VE").lower()
                print(f"[Capturado]: {texto_capturado}")
            except sr.UnknownValueError:
                continue  # Silencio o ruido no identificado, ignorar.
            except sr.RequestError:
                print("[Error de Red] Falla temporal en el puente de Google STT.")
                continue

            # ALERTA DE ACTIVACIÓN DE MATRIZ
            if WAKE_WORD in texto_capturado:
                # Limpiamos el comando quitando la palabra "tercero" para mandarle solo la orden limpia a la IA
                comando_limpio = texto_capturado.replace(WAKE_WORD, "").strip()
                
                if not comando_limpio:
                    print(f"[{WAKE_WORD.upper()} Activado]: Esperando orden específica...")
                    # Si solo dijiste "Tercero", le inyectamos un saludo para que te responda esperando comandos
                    comando_limpio = "Hola"

                print(f"📦 Enviando orden al Mainframe: '{comando_limpio}'")

                # Simulamos el envío del archivo físico empaquetado como si viniera del frontend
                # para que pase directo por Groq Whisper y se ejecute el Modo Jarvis
                try:
                    temp_input_path = "temp_input.wav"
                    # Exportamos los bytes crudos a un archivo temporal para la petición POST
                    with open(temp_input_path, "wb") as f:
                        f.write(audio.get_wav_data())

                    with open(temp_input_path, "rb") as f:
                        payload = {
                            "user_id": "ennio_master",
                            "chat_id": "ambient_session"
                        }
                        files = {
                            "file": ("grabacion.wav", f, "audio/wav")
                        }
                        
                        # Inyección directa al backend que mejoramos en el paso anterior
                        response = requests.post(URL_AUDIO_ENDPOINT, data=payload, files=files)
                        
                    if os.path.exists(temp_input_path):
                        try:
                            os.remove(temp_input_path)
                        except Exception:
                            pass

                    if response.status_code == 200:
                        data = response.json()
                        texto_ia = data.get("text")
                        audio_file = data.get("audio_file")
                        
                        print(f"🤖 [Tercero]: {texto_ia}")
                        
                        if audio_file:
                            url_completa_audio = f"{URL_STATIC_AUDIO}{audio_file}"
                            reproducir_respuesta_local(url_completa_audio)
                    else:
                        print(f"[Error Backend]: Status {response.status_code}")
                except Exception as e:
                    print(f"[Falla de Enlace]: No se pudo inyectar el paquete al core: {e}")

        except KeyboardInterrupt:
            print("\n[Tercero OS] Desconectando sistemas de escucha ambiental. Apagado seguro.")
            break
        except Exception as general_error:
            print(f"[Alerta Matriz]: Reiniciando bucle por anomalía: {general_error}")
            time.sleep(1)

if __name__ == "__main__":
    iniciar_escucha_ambiental()