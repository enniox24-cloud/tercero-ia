import os
import shutil
import uvicorn
import sqlite3
import json
from fastapi import FastAPI, UploadFile, File, Form
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

# Configuración estricta de directorios
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
    """Registra una transmisión en la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO historial_chat (user_id, role, content) VALUES (?, ?, ?)",
        (user_id, role, content)
    )
    conn.commit()
    conn.close()

def obtener_historial_memoria(user_id: str, limite: int = 10):
    """Recupera los últimos paquetes de datos del usuario para el contexto."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM historial_chat WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limite)
    )
    filas = cursor.fetchall()
    conn.close()
    
    # Invertimos el orden para que vaya de la más antigua a la más reciente
    mensajes = [{"role": f[0], "content": f[1]} for f in reversed(filas)]
    return mensajes

# Inicializamos la memoria al arrancar el servidor
inicializar_base_datos()
# ========================================================

# Montar la carpeta raíz de almacenamiento estático
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
async def root():
    return FileResponse("index.html")

# Endpoint para chat estándar con inyección de memoria persistente
@app.post("/chat")
async def chat(data: dict):
    if not core: 
        return {"text": "Sistema offline.", "audio_url": None}
    
    user_id = data.get("user_id", "ennio")
    mensaje_usuario = data.get("message", "")
    
    if not mensaje_usuario:
        return {"text": "Paquete de datos vacío.", "audio_url": None}

    # 1. Guardamos lo que Ennio acaba de decir en la base de datos
    guardar_en_memoria(user_id, "user", mensaje_usuario)
    
    # 2. Recuperamos el contexto histórico acumulado para TerceroCore
    # Nota: Si tu TerceroCore aún no procesa arreglos de historial, esto sirve de base para la Fase 3
    historial_contexto = obtener_historial_memoria(user_id, limite=10)
    
    # 3. Transmisión al procesador cognitivo central
    res = core.chat(user_id, mensaje_usuario)
    respuesta_texto = res.get("text", "")
    
    # 4. Guardamos la respuesta de Tercero en la base de datos para el futuro
    if respuesta_texto:
        guardar_en_memoria(user_id, "assistant", respuesta_texto)
    
    audio_file = res.get("audio_file")
    audio_url = f"/uploads/responses/{audio_file}" if audio_file else None
    
    return {"text": respuesta_texto, "audio_url": audio_url}

# Endpoint para subida de archivos con registro en memoria
@app.post("/upload")
async def upload_file(user_id: str = Form(...), file: UploadFile = File(...)):
    file_path = os.path.join(FILES_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    prompt_archivo = f"[SISTEMA]: El usuario ha cargado el archivo '{file.filename}'. Analízalo y confirma su recepción."
    
    # Registramos la acción del archivo en la base de datos
    guardar_en_memoria(user_id, "user", f"[Archivo Inyectado: {file.filename}]")
    
    res = core.chat(user_id, prompt_archivo)
    respuesta_texto = res.get("text", "")
    
    if respuesta_texto:
        guardar_en_memoria(user_id, "assistant", respuesta_texto)
        
    audio_file = res.get("audio_file")
    audio_url = f"/uploads/responses/{audio_file}" if audio_file else None
    
    return {"status": "success", "filename": file.filename, "text": respuesta_texto, "audio_url": audio_url}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
