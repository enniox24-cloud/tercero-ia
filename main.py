import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.core import TerceroCore

app = FastAPI()
core = TerceroCore()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Montar carpeta de archivos estáticos
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.post("/chat")
async def chat(data: dict):
    res = core.chat(data.get("user_id"), data.get("message"))
    audio_url = f"/uploads/{res.get('audio_file')}" if res.get("audio_file") else None
    return {"text": res.get("text"), "audio_url": audio_url}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
