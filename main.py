import os
import time
import threading
import json  # <-- FIX CRÍTICO: Inyección del módulo para serialización de datos

from flask import Flask, render_template, request, jsonify, Response

# IMPORTACIÓN DE LOS COMPONENTES PRINCIPALES DEL MAINFRAME
from backend.core import TerceroCore
from backend.plugins.environment import EnvironmentPlugin

app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")

# Inicialización de los núcleos centrales
core = TerceroCore()
env_monitor = EnvironmentPlugin()

# Lista de suscriptores activos para el canal SSE de telemetría
clientes_sse = []

def enviar_log_al_hud(origen: str, mensaje: str):
    """Escribe de forma segura en el flujo SSE para actualizar el HUD en vivo."""
    payload = f"data: {json.dumps({'origen': origen, 'mensaje': mensaje})}\n\n"
    for cliente in clientes_sse:
        try:
            cliente.put(payload)
        except Exception:
            pass

# Vinculamos el disparador de logs del Core con nuestro emisor local SSE
core.enviar_log_external = enviar_log_al_hud


# =====================================================================
# DEMONIO DE FONDO: HILO PERPETUO DE TELEMETRÍA Y CONTROL DE ENTORNO
# =====================================================================
def daemon_tareas_segundo_plano():
    """Hilo secundario perpetuo. Gestiona alertas de tiempo y variables ambientales."""
    print("[SISTEMA]: Demonio de fondo iniciado. Monitoreando entorno operativo...")
    
    # Contador de ciclos para no saturar la API meteorológica (consultas espaciadas)
    ciclo = 0
    
    while True:
        try:
            # 1. Monitoreo del Reloj y Alertas Horarias Estándar
            hora_actual = time.strftime("%H:%M")
            if hora_actual == "08:00":
                enviar_log_al_hud("SYSTEM", "Secuencia de inicio matutina activa. Buenos días, operador.")
                time.sleep(60) # Evita doble disparo en el mismo minuto
                
            # 2. Verificación del Módulo Ambiental de Maracaibo (Cada 30 ciclos de bucle)
            if ciclo % 30 == 0:
                telemetria_clima = env_monitor.obtener_telemetria_maracaibo()
                
                # Si el estado no es estable, inyectamos la alerta directo a la pantalla
                if telemetria_clima["estado_critico"] != "ESTABLE":
                    enviar_log_al_hud(
                        "ENVIRONMENT", 
                        f"ALERTA ATMOSFÉRICA [{telemetria_clima['temperatura']}]: {telemetria_clima['reporte_diagnostico']}"
                    )
                else:
                    # Log nominal opcional para verificar que el escáner sigue vivo
                    enviar_log_al_hud("ENVIRONMENT", f"Monitoreo nominal. Maracaibo: {telemetria_clima['temperatura']}.")
            
            # Control de incremento y reset de desbordamiento de ciclo
            ciclo = (ciclo + 1) if ciclo < 3000 else 0
            
            # Latencia base del bucle del demonio (Revisión cada 10 segundos)
            time.sleep(10)
            
        except Exception as e:
            print(f"[ANOMALÍA EN DEMONIO]: Error crítico en el hilo de fondo: {str(e)}")
            time.sleep(15) # Espera de resiliencia antes de reiniciar ciclo

# Lanzamiento del hilo asíncronono inmune a los requests del cliente
hilo_demonio = threading.Thread(target=daemon_tareas_segundo_plano, daemon=True)
hilo_demonio.start()


# =====================================================================
# RUTAS DE CONTROL DEL SERVIDOR FLASK
# =====================================================================
@app.route('/')
def index():
    """Despliega la consola de la interfaz gráfica principal (HUD)."""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Canal de comunicación síncrono con el Core de Tercero."""
    data = request.json or {}
    user_message = data.get("message", "")
    user_id = data.get("user_id", "ennio")
    
    if not user_message:
        return jsonify({"error": "Matriz de mensaje vacía"}), 400
        
    # El core procesa el enrutamiento heurístico, archivos e historial
    respuesta_mainframe = core.chat(user_id, user_message)
    return jsonify(respuesta_mainframe)

@app.route('/stream_telemetria')
def stream_telemetria():
    """Punto de acoplamiento SSE (Server-Sent Events) para el HUD del frontend."""
    import queue
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
            clientes_sse.remove(q)
            
    return Response(generar_flujo(), mimetype="text/event-stream")

if __name__ == '__main__':
    # Configuración de despliegue para desarrollo local o entornos en la nube
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
