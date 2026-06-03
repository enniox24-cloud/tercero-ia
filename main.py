import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.core import TerceroCore

app = FastAPI()
core = TerceroCore()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Configuración estricta de directorios
UPLOAD_DIR = "uploads"
FILES_DIR = os.path.join(UPLOAD_DIR, "files")
RESPONSES_DIR = os.path.join(UPLOAD_DIR, "responses")

os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(RESPONSES_DIR, exist_ok=True)

# Montar la carpeta raíz de almacenamiento estático
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    return FileResponse("index.html")

# Endpoint para chat estándar y respuesta de audio sincronizada
@app.post("/chat")
async def chat(data: dict):
    if not core: 
        return {"text": "Sistema offline.", "audio_url": None}
    
    res = core.chat(data.get("user_id"), data.get("message"))
    
    # Construcción exacta de la URL relativa para evitar el error observado en image_199.png
    audio_file = res.get("audio_file")
    audio_url = f"/uploads/responses/{audio_file}" if audio_file else None
    
    return {"text": res.get("text"), "audio_url": audio_url}

# Endpoint optimizado para subida de archivos (PDF, Imágenes)
@app.post("/upload")
async def upload_file(user_id: str = Form(...), file: UploadFile = File(...)):
    file_path = os.path.join(FILES_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Notificamos al sistema que un nuevo archivo ha sido inyectado en la matriz de datos
    prompt_archivo = f"[SISTEMA]: El usuario ha cargado el archivo '{file.filename}'. Analízalo y confirma su recepción."
    res = core.chat(user_id, prompt_archivo)
    
    audio_file = res.get("audio_file")
    audio_url = f"/uploads/responses/{audio_file}" if audio_file else None
    
    return {"status": "success", "filename": file.filename, "text": res.get("text"), "audio_url": audio_url}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
