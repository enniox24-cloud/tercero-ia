import os
import sys
import uvicorn
import logging
import psutil # Nueva dependencia para telemetría
import shutil # Nueva para limpieza
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN ---
BASE_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_PROYECTO not in sys.path:
    sys.path.insert(0, BASE_PROYECTO)

app = FastAPI(title="Tercero OS", version="3.1") # Versión actualizada

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- INICIALIZACIÓN ---
core = None
try:
    from backend.core import TerceroCore
    core = TerceroCore()
    logger.info("TerceroCore inicializado.")
except Exception as e:
    logger.error(f"FALLO CRÍTICO: {e}")

UPLOAD_DIR = os.path.join(BASE_PROYECTO, "uploads")
RESPONSES_DIR = os.path.join(UPLOAD_DIR, "responses")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESPONSES_DIR, exist_ok=True)

app.mount("/static/audio", StaticFiles(directory=RESPONSES_DIR), name="static_audio")

# --- NUEVO ENDPOINT DE TELEMETRÍA ---
@app.get("/api/telemetria")
async def get_telemetria():
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "status": "ONLINE" if core else "CORE_FAILED"
    }

@app.post("/chat-audio")
async def chat_audio(user_id: str = Form(...), chat_id: str = Form(...), file: UploadFile = File(...)):
    if not core:
        return JSONResponse(status_code=500, content={"error": "Núcleo offline."})
    
    # Ruta segura
    filepath = os.path.join(UPLOAD_DIR, f"temp_{user_id}_{file.filename}")
    
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with open(filepath, "rb") as audio_file:
            transcription = core.llm.client.audio.transcriptions.create(
                model="whisper-large-v3", file=audio_file, language="es"
            )
        
        resultado = core.chat(user_id, transcription.text)

        return {
            "user_text": transcription.text,
            "text": resultado.get("text"),
            "audio_url": f"/static/audio/{resultado.get('audio_file')}" 
        }
    except Exception as e:
        logger.error(f"Error en chat: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        # LIMPIEZA AUTOMÁTICA: Borramos el audio de entrada tras procesar
        if os.path.exists(filepath):
            os.remove(filepath)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
