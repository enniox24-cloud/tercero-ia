import os
import time
import json
import random
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from groq import Groq

# Inicialización de la App con soporte CORS completo
app = Flask(__name__)
CORS(app)

# Inicialización segura de Groq (Evita caídas si la clave no está lista)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# --- ENDPOINT 1: MONITOREO DE SALUD ---
@app.route('/health', methods=['GET'])
def health_check():
    """Ruta para que Render verifique que el backend está vivo."""
    return jsonify({
        "status": "online",
        "engine": "Flask + Gunicorn (Nativo)",
        "groq_loaded": groq_client is not None
    }), 200


# --- ENDPOINT 2: PROCESAMIENTO DE IA (GROQ) ---
@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Maneja las peticiones de texto hacia los modelos de Groq."""
    if not groq_client:
        return jsonify({"error": "La variable de entorno GROQ_API_KEY no está configurada."}), 500
    
    try:
        data = request.get_json() or {}
        user_message = data.get("message", "").strip()
        
        if not user_message:
            return jsonify({"error": "El mensaje no puede estar vacío."}), 400

        # Consulta directa a Llama 3
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Eres un asistente técnico de alta precisión. Respondes de forma clara, directa y concisa."},
                {"role": "user", "content": user_message}
            ],
            temperature=0.5,
            max_tokens=1024
        )
        
        return jsonify({
            "status": "success",
            "reply": completion.choices[0].message.content
        }), 200

    except Exception as e:
        return jsonify({"error": f"Fallo en el motor de IA: {str(e)}"}), 500


# --- ENDPOINT 3: STREAMING DE TELEMETRÍA (SSE BLINDADO) ---
@app.route('/stream_telemetria')
def stream_telemetria():
    """Envía un flujo constante de datos en tiempo real sin bloquear el servidor."""
    def generar_eventos():
        try:
            while True:
                # Estructura de datos real y limpia para telemetría
                payload = {
                    "status": "active",
                    "timestamp": int(time.time()),
                    "metrics": {
                        "system_load": round(random.uniform(5.0, 25.0), 1),
                        "memory_free_mb": random.randint(1024, 4096),
                        "network_status": "stable"
                    }
                }
                
                # Formato obligatorio estricto para Server-Sent Events (SSE)
                yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(1)  # Intervalo de 1 segundo entre transmisiones
                
        except GeneratorExit:
            # Se ejecuta automáticamente cuando el usuario cierra la pestaña o el frontend se desconecta
            print("Conexión de telemetría cerrada de forma segura por el cliente.")

    # Construcción de la respuesta con cabeceras de desbifurcación para Nginx/Render
    response = Response(generar_eventos(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['X-Accel-Buffering'] = 'no'  # CRUCIAL: Desactiva el búfer en Render
    response.headers['Connection'] = 'keep-alive'
    return response


# --- ARRANQUE LOCAL ---
if __name__ == '__main__':
    # Esto solo se ejecuta localmente (en tu VS Code). Render ignorará este bloque.
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
