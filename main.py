import os
import time
import threading
import json
import queue

from flask import Flask, render_template, request, jsonify, Response
from a2wsgi import WSGIMiddleware  # Puente obligatorio para solucionar el error de Uvicorn

# IMPORTACIÓN DE LOS COMPONENTES PRINCIPALES DE TERCERO OS
from backend.core import TerceroCore
from backend.plugins.environment import EnvironmentPlugin

# =====================================================================
# CONFIGURACIÓN DE RUTAS ABSOLUTAS (SOLUCIÓN AL TEMPLATE NOT FOUND)
# =====================================================================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "frontend", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")

# Creamos la instancia interna de Flask apuntando con precisión de ruta absoluta
flask_app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# Inicialización segura de componentes del sistema
core = TerceroCore()
env_monitor = EnvironmentPlugin()
clientes_sse = []

def enviar_log_al_hud(origen: str, mensaje: str):
    """Envía señales en tiempo real al HUD a través de Server-Sent Events (SSE)."""
    try:
        payload = f"data: {json.dumps({'origen': origen, 'mensaje': mensaje}, ensure_ascii=False)}\n\n"
        for cliente in list(clientes_sse):
            try:
                cliente.put_nowait(payload)
            except Exception:
                if cliente in clientes_sse:
                    clientes_sse.remove(cliente)
    except Exception as e:
        print(f"[ERROR SSE]: {str(e)}")

# Vinculación del canal de logs externos al núcleo
core.enviar_log_external = enviar_log_al_hud

def daemon_tareas_segundo_plano():
    """Hilo perpetuo de fondo. Monitorea el tiempo y el entorno de Maracaibo."""
    print("[SISTEMA]: Demonio de fondo activo en canal asíncrono.")
    time.sleep(10)
    ciclo = 0
    
    while True:
        try:
            hora_actual = time.strftime("%H:%M")
            if hora_actual == "08:00":
                enviar_log_al_hud("SYSTEM", "Secuencia de inicio matutina activa. Buenos días, operador.")
                time.sleep(60)
                
            if ciclo % 30 == 0:
                telemetria_clima = env_monitor.obtener_telemetria_maracaibo()
                
                if telemetria_clima and telemetria_clima.get("estado_critico") != "ESTABLE":
                    enviar_log_al_hud(
                        "ENVIRONMENT", 
                        f"ALERTA ATMOSFÉRICA [{telemetria_clima.get('temperatura')}]: {telemetria_clima.get('reporte_diagnostico')}"
                    )
                elif telemetria_clima:
                    enviar_log_al_hud("ENVIRONMENT", f"Monitoreo nominal. Maracaibo: {telemetria_clima.get('temperatura')}.")
            
            ciclo = (ciclo + 1) if ciclo < 3000 else 0
            time.sleep(10)
            
        except Exception as e:
            print(f"[ANOMALÍA DEMONIO]: {str(e)}")
            time.sleep(15)

# Activación segura del hilo secundario de monitoreo
hilo_demonio = threading.Thread(target=daemon_tareas_segundo_plano, daemon=True)
hilo_demonio.start()

# =====================================================================
# ENTORNO DE RUTAS DE LA API (WSGI INTERNO)
# =====================================================================

@flask_app.route('/')
def index():
    """Carga de la interfaz holográfica principal del HUD."""
    return render_template('index.html')

@flask_app.route('/api/chat', methods=['POST'])
def api_chat():
    """Endpoint principal de comunicación con el Mainframe."""
    try:
        data = request.json or {}
        user_message = data.get("message", "")
        user_id = data.get("user_id", "ennio")
        
        if not user_message:
            return jsonify({"error": "Matriz de mensaje vacía"}), 400
            
        respuesta_mainframe = core.chat(user_id, user_message)
        return jsonify(respuesta_mainframe)
    except Exception as e:
        return jsonify({"error": f"Fallo en comunicación: {str(e)}"}), 500

@flask_app.route('/upload', methods=['POST'])
def upload_file():
    """Endpoint para inyección y procesamiento multimedia."""
    try:
        user_id = request.form.get("user_id", "ennio")
        if 'file' not in request.files:
            return jsonify({"error": "No se detectó ningún medio en la carga"}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Nombre de archivo inválido"}), 400

        # Guardado y procesamiento seguro a través de core.py
        ruta_guardado = os.path.join(core.files_dir, file.filename)
        file.save(ruta_guardado)
        
        respuesta_mainframe = core.procesar_archivo(user_id, ruta_guardado)
        return jsonify(respuesta_mainframe)
    except Exception as e:
        return jsonify({"error": f"Fallo en inyección multimedia: {str(e)}"}), 500

@flask_app.route('/stream_telemetria')
def stream_telemetria():
    """Canal continuo SSE para logs en tiempo real sincronizados con index.html."""
    def generar_flujo():
        q = queue.Queue()
        clientes_sse.append(q)
        try:
            yield f"data: {json.dumps({'origen': 'SYSTEM', 'mensaje': 'Enlace cuántico SSE establecido con el HUD.'}, ensure_ascii=False)}\n\n"
            while True:
                msg = q.get()
                yield msg
        except GeneratorExit:
            if q in clientes_sse:
                clientes_sse.remove(q)
            
    return Response(generar_flujo(), mimetype="text/event-stream")

# =====================================================================
# INTERFLEX DE MONTAJE PARA EL ENTORNO SERVIDOR DE RENDER (ASGI WRAPPER)
# =====================================================================
# Convertimos el entorno WSGI de Flask en un ejecutable ASGI llamado 'app'.
# Esto evita por completo el error de 'start_response' con Uvicorn en producción.
app = WSGIMiddleware(flask_app)

if __name__ == '__main__':
    # Ejecución local de respaldo o fallback directo
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
