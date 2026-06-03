import os
import sys
import uvicorn
import logging
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Configuración de logs para ver errores en Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN DE RUTAS ---
BASE_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_PROYECTO not in sys.path:
    sys.path.insert(0, BASE_PROYECTO)

app = FastAPI(title="Tercero OS", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- INICIALIZACIÓN SEGURA ---
core = None
try:
    from backend.core import TerceroCore
    core = TerceroCore()
    logger.info("TerceroCore inicializado correctamente.")
except Exception as e:
    logger.error(f"FALLO CRÍTICO AL INICIALIZAR CORE: {e}")
    # No cerramos el programa, dejamos que inicie para que puedas ver el error en el log

# Directorios
UPLOAD_DIR = os.path.join(BASE_PROYECTO, "uploads")
RESPONSES_DIR = os.path.join(UPLOAD_DIR, "responses")
os.makedirs(RESPONSES_DIR, exist_ok=True)

app.mount("/static/audio", StaticFiles(directory=RESPONSES_DIR), name="static_audio")

@app.post("/chat-audio")
async def chat_audio(user_id: str = Form(...), chat_id: str = Form(...), file: UploadFile = File(...)):
    if not core:
        return JSONResponse(status_code=500, content={"error": "El núcleo no se inicializó."})
    try:
        filepath = os.path.join(UPLOAD_DIR, file.filename)
        with open(filepath, "wb") as buffer:
            buffer.write(await file.read())

        with open(filepath, "rb") as audio_file:
            transcription = core.llm.client.audio.transcriptions.create(
                model="whisper-large-v3", file=audio_file, language="es"
            )
        
        texto_transcrito = transcription.text
        resultado = core.chat(user_id, texto_transcrito)

        return {
            "user_text": texto_transcrito,
            "text": resultado.get("text"),
            "audio_file": resultado.get("audio_file"),
            "audio_url": f"/static/audio/{resultado.get('audio_file')}" 
        }
    except Exception as e:
        logger.error(f"Error en chat-audio: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
