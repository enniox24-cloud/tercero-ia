import os
import sys
import uvicorn
import logging
import psutil
import shutil
import datetime # Importante para los logs
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# ... (Mantén tus configuraciones de logs y BASE_PROYECTO igual)

# Variable global para guardar el último evento importante
ULTIMO_LOG = "Sistema iniciado correctamente en la nube."

# --- ENDPOINT DE TELEMETRÍA MEJORADO ---
@app.get("/api/telemetria")
async def get_telemetria():
    global ULTIMO_LOG
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "status": "ONLINE" if core else "CORE_FAILED",
        "serial_log": f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {ULTIMO_LOG}"
    }

@app.post("/chat-audio")
async def chat_audio(user_id: str = Form(...), chat_id: str = Form(...), file: UploadFile = File(...)):
    global ULTIMO_LOG # Para actualizar los logs desde aquí
    if not core:
        return JSONResponse(status_code=500, content={"error": "Núcleo offline."})
    
    filepath = os.path.join(UPLOAD_DIR, f"temp_{user_id}_{file.filename}")
    
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        ULTIMO_LOG = f"Procesando audio de {user_id}..."
        
        with open(filepath, "rb") as audio_file:
            transcription = core.llm.client.audio.transcriptions.create(
                model="whisper-large-v3", file=audio_file, language="es"
            )
        
        resultado = core.chat(user_id, transcription.text)
        ULTIMO_LOG = "IA: Respuesta generada con éxito."

        return {
            "user_text": transcription.text,
            "text": resultado.get("text"),
            "audio_file": resultado.get('audio_file'), # Asegúrate de devolver el nombre del archivo
            "audio_url": f"/static/audio/{resultado.get('audio_file')}" 
        }
    except Exception as e:
        ULTIMO_LOG = f"ERROR: {str(e)[:30]}" # Log corto para la consola
        logger.error(f"Error en chat: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
