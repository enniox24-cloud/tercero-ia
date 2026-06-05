import os
import time
import threading
import json
import queue

from flask import Flask, render_template, request, jsonify, Response
from a2wsgi import WSGImiddleware  # <-- EL PUENTE INTERNO CRÍTICO

# IMPORTACIÓN DE LOS COMPONENTES PRINCIPALES DEL MAINFRAME
from backend.core import TerceroCore
from backend.plugins.environment import EnvironmentPlugin

flask_app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")

# Inicialización segura de componentes del backend
core = TerceroCore()
env_monitor = EnvironmentPlugin()
clientes_sse = []

def enviar_log_al_hud(origen: str, mensaje: str):
    """Envía señales en tiempo real al HUD de forma segura."""
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

# Activación del hilo de fondo
hilo_demonio = threading.Thread(target=daemon_tareas_segundo_plano, daemon=True)
hilo_demonio.start()

@flask_app.route('/')
def index():
    return render_template('index.html')

@flask_app.route('/api/chat', methods=['POST'])
def api_chat():
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

@flask_app.route('/stream_telemetria')
def stream_telemetria():
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
# EL TRUCO MAESTRO: CONVERTIR FLASK (WSGI) A INTERFAZ ASGI PARA UVICORN
# =====================================================================
# Render busca un objeto ejecutable llamado "app". Al envolverlo con 
# WSGImiddleware, Uvicorn lo procesará perfectamente sin crasheos.
app = WSGImiddleware(flask_app)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    # Para ejecución local tradicional
    flask_app.run(host='0.0.0.0', port=port, debug=False)
