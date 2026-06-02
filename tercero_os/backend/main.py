import os
import sys
import psutil

# Mantenemos tu inyector de matriz
BASE_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_PROYECTO not in sys.path:
    sys.path.insert(0, BASE_PROYECTO)

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from backend.core import TerceroCore

app = FastAPI(title="Tercero OS", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

core = TerceroCore()

# Directorios
UPLOAD_DIR = os.path.join(BASE_PROYECTO, "uploads")
RESPONSES_DIR = os.path.join(UPLOAD_DIR, "responses")
os.makedirs(RESPONSES_DIR, exist_ok=True)

# Montaje de archivos estáticos
app.mount("/static/audio", StaticFiles(directory=RESPONSES_DIR), name="static_audio")

# --- AJUSTE CRÍTICO: CHAT Y TELEMETRÍA ---
# El resto de tu lógica de rutas está perfecta.
# Solo asegúrate de que al devolver la URL, esta incluya la raíz si es necesario.

@app.post("/chat-audio")
async def chat_audio(user_id: str = Form(...), chat_id: str = Form(...), file: UploadFile = File(...)):
    try:
        filepath = os.path.join(UPLOAD_DIR, file.filename)
        with open(filepath, "wb") as buffer:
            buffer.write(await file.read())

        # Transcripción (Tu lógica actual es correcta)
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
            # Si el teléfono sigue dando error, aquí puedes poner la URL completa si fuera necesario
            "audio_url": f"/static/audio/{resultado.get('audio_file')}" 
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- LANZAMIENTO FORZADO ---
if __name__ == "__main__":
    import uvicorn
    # AQUÍ ESTÁ EL CAMBIO PARA QUE EL TELÉFONO SE CONECTE: host="0.0.0.0"
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)