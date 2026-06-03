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
        # Invertimos el orden para conservar la línea temporal del chat
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

# ========================================================
# ENDPOINTS ADICIONALES DE TELEMETRÍA Y HISTORIAL (HUD V3)
# ========================================================
@app.get("/api/historial")
async def obtener_historial_sesion(user_id: str = "ennio"):
    """Carga de forma automatizada las transmisiones guardadas para la persistencia del HUD"""
    logs = obtener_historial_memoria(user_id, limite=15)
    return {"status": "SUCCESS", "data": logs}

@app.get("/api/telemetria/sensor/{sensor_type}")
async def generar_curva_sensor(sensor_type: str, status: str = "NORMAL"):
    """
    Genera matrices de ondas de ingeniería mecatrónica para el osciloscopio del HUD.
    Simula curvas de comportamiento físico de sensores automotrices.
    """
    puntos = 20
    x = np.linspace(0, 4 * np.pi, puntos)
    sensor_type = sensor_type.upper()
    
    if sensor_type == "MAP":
        # Sensor de Presión Absoluta del Múltiple (Voltaje típico de 0 a 5V según el vacío del motor)
        base_signal = 4.2 - (3.2 * (np.sin(x / 2) ** 2))
        if status == "FALLA":
            # Simula una fuga de vacío en la admisión o cable defectuoso (señal errática con ruido)
            base_signal += np.random.normal(0, 0.7, puntos)
            
    elif sensor_type == "IAT":
        # Sensor de Temperatura del Aire de Admisión (Curva NTC - Coeficiente de Temperatura Negativo)
        base_signal = 3.8 - (0.12 * x) + np.sin(x) * 0.15
        if status == "FALLA":
            # Simula un falso contacto eléctrico o sulfatación en el conector (cortes limpios de tensión)
            base_signal = np.array([4.8 if i % 5 == 0 else val for i, val in enumerate(base_signal)])
            
    elif sensor_type == "BATTERY":
        # Voltaje del alternador regulado (Simula la carga estable entre ~13.6V y 14.4V)
        base_signal = 13.8 + (np.sin(x * 2) * 0.25)
        if status == "FALLA":
            # Caída drástica por diodo dañado o alternador deficiente
            base_signal -= np.random.uniform(1.8, 3.2, puntos)
            
    else:
        raise HTTPException(status_code=400, detail="Módulo de sensor no configurado en el núcleo.")

    return {
        "sensor": sensor_type,
        "status": status,
        "dataset": base_signal.round(2).tolist()
    }
# ========================================================

# Endpoint optimizado para el Chat del HUD con prevención de duplicación
@app.post("/chat")
async def chat(data: dict):
    if not core: 
        return {"text": "Sistema offline.", "audio_url": None}
    
    user_id = data.get("user_id", "ennio")
    mensaje_usuario = data.get("message", "")
    
    if not mensaje_usuario:
        return {"text": "Paquete de datos vacío.", "audio_url": None}

    # 1. Procesamos la respuesta pasándole el mensaje directamente al núcleo cognitivo
    res = core.chat(user_id, mensaje_usuario)
    respuesta_texto = res.get("text", "")
    
    # 2. Una vez que el Core responde de forma aislada, guardamos AMBOS flujos en SQLite
    guardar_en_memoria(user_id, "user", mensaje_usuario)
    if respuesta_texto:
        guardar_en_memoria(user_id, "assistant", respuesta_texto)
    
    audio_file = res.get("audio_file")
    audio_url = f"/uploads/responses/{audio_file}" if audio_file else None
    
    return {"text": respuesta_texto, "audio_url": audio_url}

# Endpoint para inyección en la matriz de archivos
@app.post("/upload")
async def upload_file(user_id: str = Form(...), file: UploadFile = File(...)):
    file_path = os.path.join(FILES_DIR, file.filename)
    
    # Almacenamiento físico del script o log en la carpeta compartida
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Formateamos el interceptor exacto que TerceroCore está esperando leer con Regex
    prompt_archivo = f"El usuario ha cargado el archivo '{file.filename}'. Analízalo y confirma su recepción."
    
    # Transmisión directa al núcleo
    res = core.chat(user_id, prompt_archivo)
    respuesta_texto = res.get("text", "")
    
    # Guardamos los registros históricos de la carga del archivo
    guardar_en_memoria(user_id, "user", f"[Archivo Inyectado al Mainframe: {file.filename}]")
    if respuesta_texto:
        guardar_en_memoria(user_id, "assistant", respuesta_texto)
        
    audio_file = res.get("audio_file")
    audio_url = f"/uploads/responses/{audio_file}" if audio_file else None
    
    return {"status": "success", "filename": file.filename, "text": respuesta_texto, "audio_url": audio_url}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
