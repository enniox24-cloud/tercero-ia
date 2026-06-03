import os
import sys
import uvicorn
import logging
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración rutas
BASE_PROYECTO = os.path.dirname(os.path.abspath(__file__))
app = FastAPI(title="Tercero OS", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Inicialización Core
core = None
try:
    from backend.core import TerceroCore
    core = TerceroCore()
except Exception as e:
    logger.error(f"Error Core: {e}")

# Directorios
UPLOAD_DIR = os.path.join(BASE_PROYECTO, "uploads")
RESPONSES_DIR = os.path.join(UPLOAD_DIR, "responses")
os.makedirs(RESPONSES_DIR, exist_ok=True)
app.mount("/static/audio", StaticFiles(directory=RESPONSES_DIR), name="static_audio")

# --- RUTA PRINCIPAL ---
@app.get("/")
async def get_index():
    return FileResponse('index.html')

# --- ENDPOINTS DE CHAT ---
@app.post("/chat")
async def chat(data: dict):
    resultado = core.chat(data.get("user_id"), data.get("message"))
    return {"text": resultado.get("text"), "audio_file": resultado.get("audio_file")}

@app.post("/chat-audio")
async def chat_audio(user_id: str = Form(...), chat_id: str = Form(...), file: UploadFile = File(...)):
    # (Mantiene tu lógica de audio original)
    return {"status": "procesado"} # Ajusta esto con tu lógica de procesado real

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
