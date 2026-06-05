import os
import time
import threading
import json
import queue

from flask import Flask, render_template, request, jsonify, Response

# IMPORTACIÓN DE LOS COMPONENTES PRINCIPALES DEL MAINFRAME
from backend.core import TerceroCore
from backend.plugins.environment import EnvironmentPlugin

app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")

# Inicialización de los núcleos centrales del backend
core = TerceroCore()
env_monitor = EnvironmentPlugin()

clientes_sse = []

def enviar_log_al_hud(origen: str, mensaje: str):
    """Escribe de forma segura en el flujo SSE para actualizar el HUD en vivo."""
    try:
        payload = f"data: {json.dumps({'origen': origen, 'mensaje': mensaje}, ensure_ascii=False)}\n\n"
        for cliente in list(clientes_sse):
            try:
                cliente.put_nowait(payload)
            except Exception:
                if cliente in clientes_sse:
                    clientes_sse.remove(cliente)
    except Exception as e:
        print(f"[ERROR TRANSMISIÓN]: {str(e)}")

core.enviar_log_external = enviar_log_al_hud

def daemon_tareas_segundo_plano():
    """Hilo secundario perpetuo. Gestiona alertas de tiempo y variables ambientales."""
    print("[SISTEMA]: Demonio de fondo iniciado. Monitoreando entorno operativo...")
    
    time.sleep(5)
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
                        f"ALERTA ATMOSFÉRICA [{telemetria_clima.get('temperatura', 'N/D')}]: {telemetria_clima.get('reporte_diagnostico', '')}"
                    )
                elif telemetria_clima:
                    enviar_log_al_hud("ENVIRONMENT", f"Monitoreo nominal. Maracaibo: {telemetria_clima.get('temperatura', '32°C')}.")
            
            ciclo = (ciclo + 1) if ciclo < 3000 else 0
            time.sleep(10)
            
        except Exception as e:
            print(f"[ANOMALÍA EN DEMONIO]: Error crítico en el hilo de fondo: {str(e)}")
            time.sleep(15)

hilo_demonio = threading.Thread(target=daemon_tareas_segundo_plano, daemon=True)
hilo_demonio.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
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
        return jsonify({"error": f"Fallo en API de comunicación: {str(e)}"}), 500

@app.route('/stream_telemetria')
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
