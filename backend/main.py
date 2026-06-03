import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Inicialización segura
core = None
try:
    from backend.core import TerceroCore
    core = TerceroCore()
except:
    print("Core no encontrado, modo estático activado.")

# Ruta para servir la web
@app.get("/")
async def root():
    return FileResponse("index.html")

# Ruta para el chat
@app.post("/chat")
async def chat(data: dict):
    if core:
        res = core.chat(data.get("user_id"), data.get("message"))
        return {"text": res.get("text")}
    return {"text": "Sistema en mantenimiento, señor."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
