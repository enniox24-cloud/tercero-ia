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
os.makedirs(os.path.join(UPLOAD_DIR, "responses"), exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    return {"message": "Tercero OS Mainframe Online"}

# Generador de telemetría optimizado (Cero dependencias externas)
@app.get("/api/telemetria/sensor/{sensor_type}")
async def generar_curva_sensor(sensor_type: str, status: str = "NORMAL"):
    puntos = 20
    s_type = sensor_type.upper()
    # Generamos los datos con matemática nativa
    x_vals = [i * (6.28 / 19.0) for i in range(puntos)]
    
    if s_type == "MAP":
        data = [2.5 + math.sin(x) for x in x_vals]
    elif s_type == "BATTERY":
        data = [13.8 + (random.uniform(-0.2, 0.2)) for _ in range(puntos)]
    else:
        data = [850 + (math.sin(x) * 50) for x in x_vals]
        
    return {"dataset": [round(val, 2) for val in data]}

@app.post("/chat")
async def chat(data: dict):
    # Aseguramos que el chat siempre devuelva la estructura esperada
    res = core.chat(data.get("user_id", "Ennio"), data.get("message", ""))
    return res

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
