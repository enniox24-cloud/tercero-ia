import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Importación del núcleo
try:
    from backend.core import TerceroCore
    core = TerceroCore()
except Exception as e:
    print(f"Error cargando Core: {e}")
    core = None

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Servir archivos estáticos (audios, imagenes)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.post("/chat")
async def chat(data: dict):
    if not core: return {"text": "Sistema offline."}
    res = core.chat(data.get("user_id"), data.get("message"))
    return {"text": res.get("text"), "audio_url": res.get("audio_file")}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
