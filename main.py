import os
import time
import threading
import json
import queue

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
    payload = f"data: {json.dumps({'origen': origen, 'mensaje': mensaje})}\n\n"
    # Recorremos una copia de la lista para evitar errores de concurrencia en producción
    for cliente in list(clientes_sse):
        try:
            cliente.put_nowait(payload)
        except Exception:
            if cliente in clientes_sse:
                clientes_sse.remove(cliente)

# Vinculamos el disparador de logs del Core con nuestro emisor local SSE
core.enviar_log_external = enviar_log_al_hud


# =====================================================================
# DEMONIO DE FONDO: HILO PERPETUO DE TELEMETRÍA Y CONTROL DE ENTORNO
# =====================================================================
def daemon_tareas_segundo_plano():
    """Hilo secundario perpetuo. Gestiona alertas de tiempo y variables ambientales."""
    print("[SISTEMA]: Demonio de fondo iniciado. Monitoreando entorno operativo...")
    
    # Contador de ciclos para espaciar las llamadas climáticas de Maracaibo
    ciclo = 0
    
    while True:
        try:
            # 1. Monitoreo del Reloj y Alertas Horarias Estándar
            hora_actual = time.strftime("%H:%M")
            if hora_actual == "08:00":
                enviar_log_al_hud("SYSTEM", "Secuencia de inicio matutina activa. Buenos días, operador.")
                time.sleep(60)  # Evita doble disparo en el mismo minuto
                
            # 2. Verificación del Módulo Ambiental de Maracaibo (Cada 30 ciclos = 5 minutos)
            if ciclo % 30 == 0:
                telemetria_clima = env_monitor.obtener_telemetria_maracaibo()
                
                # Si el estado no es estable, inyectamos la alerta directo a la pantalla
                if telemetria_clima and telemetria_clima.get("estado_critico") != "ESTABLE":
                    enviar_log_al_hud(
                        "ENVIRONMENT", 
                        f"ALERTA ATMOSFÉRICA [{telemetria_clima.get('temperatura', 'N/D')}]: {telemetria_clima.get('reporte_diagnostico', '')}"
                    )
                elif telemetria_clima:
                    # Log nominal para verificar que el escáner del entorno sigue en línea
                    enviar_log_al_hud("ENVIRONMENT", f"Monitoreo nominal. Maracaibo: {telemetria_clima.get('temperatura', '32°C')}.")
            
            # Control de incremento y reset de desbordamiento de ciclo
            ciclo = (ciclo + 1) if ciclo < 3000 else 0
            
            # Latencia base del bucle del demonio (Revisión cada 10 segundos)
            time.sleep(10)
            
        except Exception as e:
            print(f"[ANOMALÍA EN DEMONIO]: Error crítico en el hilo de fondo: {str(e)}")
            time.sleep(15)  # Espera de resiliencia antes de reiniciar ciclo

# Lanzamiento del hilo asíncrono inmune a los requests http
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
            
        # El core procesa el enrutamiento heurístico, archivos e historial
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
            # Enviamos ping inicial de sincronización con el cliente web
            yield f"data: {json.dumps({'origen': 'SYSTEM', 'mensaje': 'Enlace cuántico SSE establecido con el HUD.'})}\n\n"
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
    # Configuración de puerto dinámica adaptada a Render y entorno local
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
