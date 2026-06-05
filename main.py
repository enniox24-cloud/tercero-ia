import os
import queue
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

# Inyectamos la función de logs dentro del core de forma dinámica para no romper el acoplamiento
core.enviar_log_external = enviar_log_al_hud

@app.route('/')
def index():
    """Sirve la interfaz del HUD Jarvis desde el frontend."""
    return render_template('index.html')

@app.route('/chat', py-yield-supported=True, methods=['POST'])
def chat():
    """Procesa las interacciones de texto y voz del operador."""
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({"text": "Error: Datos de transmisión corruptos.", "audio_url": None}), 400
            
        user_id = datos.get("user_id", "ennio")
        mensaje = datos.get("message", "")
        
        enviar_log_al_hud("SYSTEM", "Abriendo socket de comunicación... Analizando variables de entorno.")
        
        # Interceptamos si hay palabras clave para alertar al HUD antes de que el LLM responda
        msg_lower = mensaje.lower()
        if any(k in msg_lower for k in ["calculo", "algebra", "codigo", "python", "sensor", "iat", "map", "v8", "guaya"]):
            enviar_log_al_hud("SYSTEM", "Alerta de datos técnicos detectada. Despachando Agente ALPHA.")
        elif any(k in msg_lower for k in ["abrir", "youtube", "spotify", "frullato", "negocio", "ropa", "whatsapp"]):
            enviar_log_al_hud("SYSTEM", "Comando de control/gestión detectado. Despachando Agente BRAVO.")

        # Ejecución del procesamiento en el Core
        resultado = core.chat(user_id, mensaje)
        
        # Estructuramos la URL pública para el archivo de audio generado
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
        
        # Aseguramos el directorio físico en el contenedor de Render
        os.makedirs(core.files_dir, exist_ok=True)
        archivo.save(ruta_destino)
        
        enviar_log_al_hud("SYSTEM", f"Archivo '{nombre_archivo}' inyectado con éxito en disco. Decodificando metadatos visuales...")
        
        # Simulamos la orden enviando el trigger estructurado al core
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

# ========================================================
# NUEVO ENDPOINT CUÁNTICO: TRANSMISIÓN DE LOGS EN VIVO (SSE)
# ========================================================
@app.route('/stream-telemetry')
def stream_telemetry():
    """Mantiene un canal abierto para enviar señales en vivo al HUD del frontend."""
    def event_stream():
        while True:
            # Espera indefinidamente hasta que entre una nueva señal de log
            payload = log_queue.get()
            yield f"data: {json.dumps(payload)}\n\n"
            
    return Response(event_stream(), mimetype="text/event-stream")

if __name__ == '__main__':
    # Configuración de puerto adaptable para la infraestructura de Render
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=puerto, debug=False)
