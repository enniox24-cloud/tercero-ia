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

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Configuración de rutas de almacenamiento
UPLOAD_DIR = "uploads"
FILES_DIR = os.path.join(UPLOAD_DIR, "files")
RESPONSES_DIR = os.path.join(UPLOAD_DIR, "responses")

os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(RESPONSES_DIR, exist_ok=True)

# Montar carpeta de archivos estáticos para que sean accesibles desde la web
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    return FileResponse("index.html")

# Endpoint para chat estándar
@app.post("/chat")
async def chat(data: dict):
    res = core.chat(data.get("user_id"), data.get("message"))
    audio_url = f"/uploads/responses/{res.get('audio_file')}" if res.get("audio_file") else None
    return {"text": res.get("text"), "audio_url": audio_url}

# Endpoint para subida de archivos (PDF, Imágenes)
@app.post("/upload")
async def upload_file(user_id: str = Form(...), file: UploadFile = File(...)):
    file_path = os.path.join(FILES_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Aquí puedes añadir lógica para que el Core analice el archivo
    return {"status": "success", "filename": file.filename}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
