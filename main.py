import os
import shutil
import uvicorn
import sqlite3
import json
import numpy as np
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.core import TerceroCore

app = FastAPI()
core = TerceroCore()

# Middleware CORS para enlaces seguros de telemetría y audio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Configuración estricta de directorios en el Mainframe
UPLOAD_DIR = "uploads"
FILES_DIR = os.path.join(UPLOAD_DIR, "files")
RESPONSES_DIR = os.path.join(UPLOAD_DIR, "responses")
DB_PATH = "tercero_memory.db"

os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(RESPONSES_DIR, exist_ok=True)

# ========================================================
# MOTOR DE MEMORIA CUÁNTICA PERSISTENTE (SQLite)
# ========================================================
def inicializar_base_datos():
    """Crea la tabla de memoria si no existe en el mainframe."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def guardar_en_memoria(user_id: str, role: str, content: str):
    """Registra una transmisión de datos de manera física en SQLite."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO historial_chat (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR SQLITE WRITE]: No se pudo escribir en la memoria: {str(e)}")

def obtener_historial_memoria(user_id: str, limite: int = 15):
    """Recupera los últimos paquetes de datos ordenados cronológicamente."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM historial_chat WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limite)
        )
        filas = cursor.fetchall()
        conn.close()
        return [{"role": f[0], "content": f[1]} for f in reversed(filas)]
    except Exception:
        return []

# Inicializamos el mainframe de memoria al arrancar la aplicación
inicializar_base_datos()
# ========================================================

# Montar la carpeta raíz de almacenamiento estático para descargas de audio y visuales
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    return FileResponse("index.html")

# Endpoint para cargar el historial de diagnósticos previos al encender el HUD
@app.get("/api/historial")
async def obtener_historial_sesion(user_id: str = "Ennio"):
    return {"status": "SUCCESS", "data": obtener_historial_memoria(user_id, limite=15)}

# Endpoint generador de señales físicas para mecatrónica de automoción
@app.get("/api/telemetria/sensor/{sensor_type}")
async def generar_curva_sensor(sensor_type: str, status: str = "NORMAL"):
    puntos = 20
    x = np.linspace(0, 4 * np.pi, puntos)
    sensor_type = sensor_type.upper()
    
    if sensor_type == "MAP":
        # Sensor MAP (Presión absoluta en múltiple de admisión, rango de 0V a 5V)
        base_signal = 4.2 - (3.2 * (np.sin(x / 2) ** 2))
        if status == "FALLA":
            # Ruido por fuga de vacío o cable de señal suelto
            base_signal += np.random.normal(0, 0.7, puntos)
            
    elif sensor_type == "IAT":
        # Sensor IAT (Temperatura de aire de admisión, termistor NTC)
        base_signal = 3.8 - (0.12 * x) + np.sin(x) * 0.15
        if status == "FALLA":
            # Simula cortes por conector sulfatado
            base_signal = np.array([4.8 if i % 5 == 0 else val for i, val in enumerate(base_signal)])
            
    elif sensor_type == "BATTERY":
        # Sistema de Carga (Voltaje nominal entre 13.8V y 14.4V)
        base_signal = 13.8 + (np.sin(x * 2) * 0.25)
        if status == "FALLA":
            # Caída drástica por alternador deficiente
            base_signal -= np.random.uniform(1.8, 3.2, puntos)
            
    else:
        raise HTTPException(status_code=400, detail="Sensor inválido.")

    return {
        "sensor": sensor_type,
        "status": status,
        "dataset": base_signal.round(2).tolist()
    }

# Endpoint central para procesamiento de chat del Mainframe
@app.post("/chat")
async def chat(data: dict):
    if not core: 
        return {"text": "Sistema offline.", "audio_url": None}
    
    user_id = data.get("user_id", "Ennio")
    mensaje_usuario = data.get("message", "")
    if not mensaje_usuario: 
        return {"text": "Paquete vacío.", "audio_url": None}

    # Procesamos la respuesta llamando al núcleo cognitivo
    res = core.chat(user_id, mensaje_usuario)
    respuesta_texto = res.get("text", "")
    
    # Registramos transacciones de datos físicas en SQLite
    guardar_en_memoria(user_id, "user", mensaje_usuario)
    if respuesta_texto:
        guardar_en_memoria(user_id, "assistant", respuesta_texto)
    
    audio_file = res.get("audio_file")
    audio_url = f"/uploads/responses/{audio_file}" if audio_file else None
    
    # Enviamos la respuesta junto con las banderas de comportamiento gráfico para el HUD
    return {
        "text": respuesta_texto, 
        "audio_url": audio_url,
        "telemetry_mode": res.get("telemetry_mode", "BATTERY"),
        "telemetry_status": res.get("telemetry_status", "NORMAL")
    }

# Endpoint de matriz para subida y procesamiento de archivos de error o logs
@app.post("/upload")
async def upload_file(user_id: str = Form(...), file: UploadFile = File(...)):
    file_path = os.path.join(FILES_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    prompt_archivo = f"El usuario ha cargado el archivo '{file.filename}'. Analízalo y confirma su recepción."
    res = core.chat(user_id, prompt_archivo)
    respuesta_texto = res.get("text", "")
    
    guardar_en_memoria(user_id, "user", f"[Archivo Inyectado: {file.filename}]")
    if respuesta_texto: 
        guardar_en_memoria(user_id, "assistant", respuesta_texto)
        
    audio_file = res.get("audio_file")
    audio_url = f"/uploads/responses/{audio_file}" if audio_file else None
    return {"status": "success", "filename": file.filename, "text": respuesta_texto, "audio_url": audio_url}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
