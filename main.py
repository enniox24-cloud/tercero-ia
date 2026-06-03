import os
import shutil
import uvicorn
import sqlite3
import math
import random
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.core import TerceroCore

app = FastAPI()
core = TerceroCore()

# Configuración de carpetas
UPLOAD_DIR = "uploads"
FILES_DIR = os.path.join(UPLOAD_DIR, "files")
os.makedirs(FILES_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    return {"message": "Tercero OS Mainframe Online"}

# Generador de telemetría SIN numpy (usando math nativo)
@app.get("/api/telemetria/sensor/{sensor_type}")
async def generar_curva_sensor(sensor_type: str):
    puntos = 20
    # Generamos una onda senoidal básica usando math nativo
    dataset = [13.0 + math.sin(i * 0.5) for i in range(puntos)]
    return {"dataset": [round(val, 2) for val in dataset]}

@app.post("/chat")
async def chat(data: dict):
    res = core.chat(data.get("user_id"), data.get("message"))
    return res

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
