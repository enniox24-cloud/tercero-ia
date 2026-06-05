import os
import time
import threading
import json
import queue  # IMPORTACIÓN GLOBAL: Evita que los hilos colapsen en frío

from flask import Flask, render_template, request, jsonify, Response

# IMPORTACIÓN DE LOS COMPONENTES PRINCIPALES DEL MAINFRAME
from backend.core import TerceroCore
from backend.plugins.environment import EnvironmentPlugin

# Inicialización de la infraestructura del Servidor Flask
app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")

# Inicialización de los núcleos centrales del backend
core = TerceroCore()
env_monitor = EnvironmentPlugin()

# Matriz de conexiones activas para el canal SSE del HUD
clientes_sse = []

def enviar_log_al_hud(origen: str, mensaje: str):
    """Escribe de forma segura en el flujo SSE para actualizar el HUD en vivo."""
    try:
        payload = f"data: {json.dumps({'origen': origen, 'mensaje': mensaje}, ensure_ascii=False)}\n\n"
        # Usamos una lista limpia para evitar errores de mutación durante el bucle
        for cliente in list(clientes_sse):
            try:
                cliente.put_nowait(payload)
            except Exception:
                if cliente in clientes_sse:
                    clientes_sse.remove(cliente)
    except Exception as e:
        print(f"[ERROR TRANSMISIÓN]: {str(e)}")

# Vinculamos el disparador de logs del Core con nuestro emisor local SSE
core.enviar_log_external = enviar_log_al_hud


# =====================================================================
# DEMONIO DE FONDO: HILO PERPETUO DE TELEMETRÍA Y CONTROL DE ENTORNO
# =====================================================================
def daemon_tareas_segundo_plano():
    """Hilo secundario perpetuo. Gestiona alertas de tiempo y variables ambientales."""
    print("[SISTEMA]: Demonio de fondo iniciado. Monitoreando entorno operativo...")
    
    # Damos un margen de 5 segundos para que Flask levante por completo antes de iniciar escaneos
    time.sleep(5)
    ciclo = 0
    
    while True:
        try:
            # 1. Monitoreo del Reloj y Alertas Horarias Estándar
            hora_actual = time.strftime("%H:%M")
            if hora_actual == "08:00":
                enviar_log_al_hud("SYSTEM", "Secuencia de inicio matutina activa. Buenos días, operador.")
                time.sleep(60)
                
            # 2. Verificación del Módulo Ambiental de Maracaibo (Cada 30 ciclos = 5 minutos)
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

# Lanzamiento del hilo asíncrono seguro
hilo_demonio = threading.Thread(target=daemon_tareas_segundo_plano, daemon=True)
hilo_demonio.start()


# =====================================================================
# RUTAS DE CONTROL DEL SERVIDOR FLASK (HUD INTERFACE)
# =====================================================================
@app.route('/')
def index():
    """Despliega la consola de la interfaz gráfica principal (HUD)."""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Canal de comunicación síncrono con el Core de Tercero OS."""
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
    """Punto de acoplamiento SSE (Server-Sent Events) para el HUD del frontend."""
    def generar_flujo():
        q = queue.Queue()
        clientes_sse.append(q)
        try:
            # Ping de sincronización inicial
            yield f"data: {json.dumps({'origen': 'SYSTEM', 'mensaje': 'Enlace cuántico SSE establecido con el HUD.'}, ensure_ascii=False)}\n\n"
            while True:
                msg = q.get()
                yield msg
        except GeneratorExit:
            if q in clientes_sse:
                clientes_sse.remove(q)
            
    return Response(generar_flujo(), mimetype="text/event-stream")


# =====================================================================
# ARRANQUE DE SEGURIDAD
# =====================================================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
