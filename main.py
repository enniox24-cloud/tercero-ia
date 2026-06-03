import os
import shutil
import uvicorn
import sqlite3
import math
import random
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.core import TerceroCore

app = FastAPI()
core = TerceroCore()

# Configuración de carpetas
UPLOAD_DIR = "uploads"
FILES_DIR = os.path.join(UPLOAD_DIR, "files")
os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "responses"), exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    # Aquí cargamos la interfaz visual automáticamente
    return FileResponse("index.html")

@app.get("/api/telemetria/sensor/{sensor_type}")
async def generar_curva_sensor(sensor_type: str, status: str = "NORMAL"):
    # Generación nativa sin dependencias externas
    puntos = 20
    x = [i * 0.3 for i in range(puntos)]
    if sensor_type.upper() == "MAP":
        data = [2.5 + math.sin(val) for val in x]
    else:
        data = [13.8 + (random.random() * 0.1) for _ in range(puntos)]
    return {"dataset": [round(val, 2) for val in data]}

@app.post("/chat")
async def chat(data: dict):
    return core.chat(data.get("user_id", "Ennio"), data.get("message", ""))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
