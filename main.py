import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.core import TerceroCore

app = FastAPI(title="Tercero OS V6")
core = TerceroCore()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Configuración de rutas
UPLOAD_DIR = "uploads"
os.makedirs(os.path.join(UPLOAD_DIR, "files"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.post("/chat")
async def chat_endpoint(data: dict):
    return await core.procesar_peticion(data.get("user_id", "Ennio"), data.get("message", ""))

@app.post("/upload")
async def upload(user_id: str = Form(...), file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, "files", file.filename)
    with open(path, "wb") as f:
        f.write(await file.read())
    return await core.procesar_peticion(user_id, f"Archivo inyectado: {file.filename}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
