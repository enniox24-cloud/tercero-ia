import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.core import TerceroCore

app = FastAPI()
core = TerceroCore()

UPLOAD_DIR = "uploads"
FILES_DIR = os.path.join(UPLOAD_DIR, "files")
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "responses"), exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.post("/chat")
async def chat(data: dict):
    # Aquí reactivamos el motor de inteligencia de Tercero
    return core.chat(data.get("user_id", "Ennio"), data.get("message", ""))

@app.post("/upload")
async def upload_file(user_id: str = Form(...), file: UploadFile = File(...)):
    # Aquí reactivamos la carga de archivos (PDFs, logs, etc.)
    file_path = os.path.join(FILES_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Enviamos un aviso a Tercero de que recibió un archivo
    return core.chat(user_id, f"El usuario ha cargado el archivo '{file.filename}'. Analízalo.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
