import os
import queue
import time
import threading
import json
from flask import Flask, request, jsonify, render_template, Response
from backend.core import TerceroCore

app = Flask(__name__, template_folder="../frontend", static_folder="../frontend")

# Inicialización del núcleo central de Tercero OS
core = TerceroCore()

# Cola global asíncrona para transmitir logs en tiempo real al HUD
log_queue = queue.Queue()

def enviar_log_al_hud(origen: str, mensaje: str):
    """Inserta una señal de telemetría en la cola para que el frontend la imprima al instante."""
    payload = {"origen": origen, "texto": mensaje}
    log_queue.put(payload)

# Inyectamos la función de logs dentro del core de forma dinámica
core.enviar_log_external = enviar_log_al_hud

# ========================================================
# HILO ASÍNCRONO DE TELEMETRÍA PROACTIVA (DEMONIO CRON)
# ========================================================
def daemon_tareas_segundo_plano():
    """Bucle perpetuo de fondo que vigila el sistema y envía alertas proactivas al HUD."""
    print("[SISTEMA]: Demonio de resiliencia y tareas asíncronas inicializado.")
    time.sleep(10)  # Espera inicial a que el frontend se conecte al SSE
    
    contador = 0
    while True:
        try:
            # Cada 30 minutos de ejecución simula un reporte de estado del Mainframe
            if contador % 60 == 0 and contador > 0:
                enviar_log_al_hud("SYSTEM", "CRON_DAEMON: Diagnóstico térmico estable. Núcleos cuánticos operando al 100%.")
            
            # Alertas proactivas simuladas basadas en el contexto del operador (puedes expandir esto con fechas reales)
            # Ejemplo de alerta de rutina matutina o recordatorio académico inyectado al HUD
            ahora = time.strftime("%H:%M")
            if ahora == "08:00":
                enviar_log_al_hud("ACTIVATION", "CRON_ALERT: Bloque académico activo. Revisar asignaciones de Ingeniería en Mecatrónica (URBE).")
            elif ahora == "14:00":
                enviar_log_al_hud("ACTIVATION", "CRON_ALERT: Bloque comercial activo. Monitorear inventario y recetas en Frullato.")
                
            time.sleep(30)  # Ciclo de verificación cada 30 segundos
            contador += 1
        except Exception as e:
            print(f"[ERROR DAEMON]: {str(e)}")
            time.sleep(10)

# Lanzamos el demonio de fondo en un hilo aislado para que no bloquee las peticiones HTTP de Flask
thread_proactivo = threading.Thread(target=daemon_tareas_segundo_plano, daemon=True)
thread_proactivo.start()
# ========================================================

@app.route('/')
def index():
    """Sirve la interfaz del HUD Jarvis desde el frontend."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Procesa las interacciones de texto y voz del operador."""
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({"text": "Error: Datos de transmisión corruptos.", "audio_url": None}), 400
            
        user_id = datos.get("user_id", "ennio")
        mensaje = datos.get("message", "")
        
        enviar_log_al_hud("SYSTEM", "Abriendo socket de comunicación... Analizando variables de entorno.")
        
        # Interceptamos palabras clave para alertar al HUD antes de que el LLM responda
        msg_lower = mensaje.lower()
        if any(k in msg_lower for k in ["calculo", "algebra", "codigo", "python", "sensor", "iat", "map", "v8", "guaya", "matematicas", "parcial"]):
            enviar_log_al_hud("SYSTEM", "Alerta de datos técnicos detectada. Despachando Agente ALPHA.")
        elif any(k in msg_lower for k in ["abrir", "youtube", "spotify", "frullato", "negocio", "ropa", "logistica", "tienda", "whatsapp"]):
            enviar_log_al_hud("SYSTEM", "Comando de control/gestión detectado. Despachando Agente BRAVO.")

        # Ejecución del procesamiento en el Core
        resultado = core.chat(user_id, mensaje)
        
        audio_url = f"/audio/{resultado['audio_file']}" if resultado.get("audio_file") else None
        
        return jsonify({
            "text": resultado["text"],
            "audio_url": audio_url
        })
        
    except Exception as e:
        enviar_log_al_hud("SYSTEM", f"CRITICAL FAILURE en pasarela web: {str(e)}")
        return jsonify({"text": f"Fallo de enlace en app.py: {str(e)}", "audio_url": None}), 500

@app.route('/upload', methods=['POST'])
def upload():
    """Gestiona la inyección multimedia (Capturas de pantalla, códigos, PDFs)."""
    try:
        user_id = request.form.get("user_id", "ennio")
        archivo = request.files.get("file")
        
        if not archivo:
            return jsonify({"text": "Error: Matriz de archivo vacía.", "audio_url": None}), 400
            
        nombre_archivo = archivo.filename
        ruta_destino = os.path.join(core.files_dir, nombre_archivo)
        
        os.makedirs(core.files_dir, exist_ok=True)
        archivo.save(ruta_destino)
        
        enviar_log_al_hud("SYSTEM", f"Archivo '{nombre_archivo}' inyectado con éxito en disco. Decodificando metadatos visuales...")
        
        mensaje_estructurado = f"El usuario ha cargado el archivo '{nombre_archivo}' para su análisis inmediato."
        resultado = core.chat(user_id, mensaje_estructurado)
        
        audio_url = f"/audio/{resultado['audio_file']}" if resultado.get("audio_file") else None
        
        return jsonify({
            "text": resultado["text"],
            "audio_url": audio_url
        })
        
    except Exception as e:
        enviar_log_al_hud("SYSTEM", f"Fallo en inyector multimedia: {str(e)}")
        return jsonify({"text": f"Fallo crítico en upload: {str(e)}", "audio_url": None}), 500

@app.route('/audio/<filename>')
def servir_audio(filename):
    """Transmite los buffers binarios de voz al reproductor del HUD."""
    ruta_audio = os.path.join(os.getcwd(), filename)
    if os.path.exists(ruta_audio):
        def generar_stream():
            with open(ruta_audio, "rb") as f:
                data = f.read(1024)
                while data:
                    yield data
                    data = f.read(1024)
        return Response(generar_stream(), mimetype="audio/mp3")
    else:
        return "Audio no localizado en el búfer temporal", 404

@app.route('/stream-telemetry')
def stream_telemetry():
    """Mantiene un canal abierto para enviar señales en vivo al HUD del frontend."""
    def event_stream():
        while True:
            payload = log_queue.get()
            yield f"data: {json.dumps(payload)}\n\n"
            
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto, debug=False)
