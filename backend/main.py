import os
import sys
import uvicorn
import logging
import psutil
import shutil
import datetime
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse # Necesario para la interfaz
from fastapi.staticfiles import StaticFiles

# --- CONFIGURACIÓN DE RUTAS ---
BASE_PROYECTO = os.path.dirname(os.path.abspath(__file__))
# Si tu backend está en otra carpeta, ajusta esto:
sys.path.insert(0, BASE_PROYECTO)

app = FastAPI(title="Tercero OS", version="3.1")

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
except Exception as e:
    logging.error(f"FALLO CRÍTICO: {e}")

# --- CARPETAS ---
UPLOAD_DIR = os.path.join(BASE_PROYECTO, "uploads")
RESPONSES_DIR = os.path.join(UPLOAD_DIR, "responses")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESPONSES_DIR, exist_ok=True)

# Servir archivos estáticos
app.mount("/static/audio", StaticFiles(directory=RESPONSES_DIR), name="static_audio")
# Si tienes tus archivos CSS/JS en una carpeta llamada 'static', monta también:
# app.mount("/static", StaticFiles(directory="static"), name="static")

ULTIMO_LOG = "Sistema inicializado. Núcleo listo."

# --- RUTA PRINCIPAL (LA QUE HACE QUE SE VEA TU DISEÑO) ---
@app.get("/")
async def get_index():
    # Asume que tu index.html está en la raíz o en una carpeta llamada 'static'
    return FileResponse('index.html')

# --- TELEMETRÍA ---
@app.get("/api/telemetria")
async def get_telemetria():
    global ULTIMO_LOG
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "status": "ONLINE" if core else "CORE_FAILED",
        "serial_log": f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {ULTIMO_LOG}"
    }

# --- CHAT AUDIO ---
@app.post("/chat-audio")
async def chat_audio(user_id: str = Form(...), chat_id: str = Form(...), file: UploadFile = File(...)):
    global ULTIMO_LOG
    if not core: return JSONResponse(status_code=500, content={"error": "Núcleo offline."})
    
    filepath = os.path.join(UPLOAD_DIR, f"temp_{user_id}_{file.filename}")
    try:
        with open(filepath, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
        ULTIMO_LOG = f"Procesando audio: {user_id}..."
        
        with open(filepath, "rb") as audio_file:
            transc = core.llm.client.audio.transcriptions.create(model="whisper-large-v3", file=audio_file, language="es")
        
        res = core.chat(user_id, transc.text)
        ULTIMO_LOG = "IA: Respuesta generada."
        return {"user_text": transc.text, "text": res.get("text"), "audio_url": f"/static/audio/{res.get('audio_file')}"}
    except Exception as e:
        ULTIMO_LOG = "Error crítico en procesamiento."
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if os.path.exists(filepath): os.remove(filepath)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
