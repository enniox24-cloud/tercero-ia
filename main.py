import os
import time
import threading
import json
import queue

from flask import Flask, request, jsonify, Response
from a2wsgi import WSGIMiddleware  # Puente obligatorio para solucionar el error de Uvicorn

# IMPORTACIÓN DE LOS COMPONENTES PRINCIPALES DE TERCERO OS
from backend.core import TerceroCore
from backend.plugins.environment import EnvironmentPlugin

# Creamos la instancia interna de Flask sin carpetas externas (usamos renderizado directo)
flask_app = Flask(__name__)

# Inicialización segura de componentes del sistema
core = TerceroCore()
env_monitor = EnvironmentPlugin()
clientes_sse = []

# =====================================================================
# INTERFAZ HOLOGRÁFICA EN MEMORIA (HTML INCUSTADO CONTRA TEMPLATE NOT FOUND)
# =====================================================================
HTML_HUD = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TERCERO OS - MAINFRAME V9.0</title>
    <style>
        :root {
            --neon-blue: #00f2fe;
            --terminal-bg: #030508;
            --panel-border: rgba(0, 242, 254, 0.3);
            --text-color: #e0f7fc;
            --listening-red: #ff4d4f;
            --matrix-glow: rgba(0, 242, 254, 0.15);
        }
        body {
            background-color: var(--terminal-bg);
            color: var(--text-color);
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            height: 100vh;
            box-sizing: border-box;
            overflow: hidden;
            position: relative;
        }
        body::before {
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(rgba(18, 30, 49, 0.1) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
            background-size: 100% 4px, 6px 100%;
            z-index: -1;
            pointer-events: none;
        }
        #mainframe-header {
            border-bottom: 2px solid var(--neon-blue);
            padding-bottom: 12px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            text-shadow: 0 0 15px var(--neon-blue);
            font-weight: bold;
            letter-spacing: 2px;
        }
        #console-container {
            flex: 1;
            border: 1px solid var(--panel-border);
            background: rgba(4, 12, 24, 0.75);
            border-radius: 6px;
            padding: 25px;
            overflow-y: auto;
            box-shadow: inset 0 0 30px rgba(0, 242, 254, 0.1), 0 0 20px rgba(0, 0, 0, 0.8);
            margin-bottom: 20px;
            backdrop-filter: blur(4px);
        }
        .log-entry {
            margin-bottom: 14px;
            line-height: 1.6;
            animation: fadeIn 0.25s ease-out;
            font-size: 15px;
        }
        .user-log { color: #85a5ff; text-shadow: 0 0 5px rgba(133, 165, 255, 0.3); }
        .tercero-log { color: var(--neon-blue); text-shadow: 0 0 8px rgba(0, 242, 254, 0.4); }
        .system-log { color: #ffb969; text-shadow: 0 0 8px rgba(255, 185, 105, 0.4); }
        .critical-log { color: var(--listening-red); font-weight: bold; text-shadow: 0 0 10px var(--listening-red); }
        .activation-log { color: #52c41a; font-weight: bold; text-shadow: 0 0 12px rgba(82, 196, 26, 0.6); }
        #input-panel {
            display: flex;
            gap: 12px;
            background: rgba(2, 6, 12, 0.9);
            padding: 12px 20px;
            border: 1px solid var(--panel-border);
            border-radius: 6px;
            align-items: center;
            box-shadow: 0 0 25px rgba(0, 242, 254, 0.05);
        }
        #input-command {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--neon-blue);
            font-family: 'Courier New', monospace;
            font-size: 16px;
            outline: none;
            letter-spacing: 1px;
        }
        #input-command::placeholder { color: rgba(0, 242, 254, 0.4); }
        .action-btn {
            background: rgba(0, 242, 254, 0.03);
            border: 1px solid var(--neon-blue);
            color: var(--neon-blue);
            padding: 10px 24px;
            cursor: pointer;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.25s ease-in-out;
            border-radius: 4px;
        }
        .action-btn:hover {
            background: var(--neon-blue);
            color: var(--terminal-bg);
            box-shadow: 0 0 20px var(--neon-blue);
            transform: translateY(-1px);
        }
        #voice-indicator {
            width: 14px;
            height: 14px;
            background-color: rgba(0, 242, 254, 0.2);
            border: 1px solid var(--neon-blue);
            border-radius: 50%;
            margin-right: 8px;
            transition: all 0.4s ease;
        }
        #voice-indicator.active {
            background-color: var(--listening-red);
            border-color: var(--listening-red);
            box-shadow: 0 0 15px var(--listening-red), inset 0 0 5px #fff;
            animation: pulse 1s infinite alternate;
        }
        #hidden-file-input { display: none; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { from { transform: scale(1); opacity: 0.8; } to { transform: scale(1.2); opacity: 1; } }
    </style>
</head>
<body>
    <div id="mainframe-header">
        <div>// TERCERO OS // V9.0_JARVIS_HUD</div>
        <div id="system-status">STATUS: CONNECTING_TO_STREAM...</div>
    </div>
    <div id="console-container">
        <div class="log-entry tercero-log">[TERCERO OS]: Interfaz Holográfica iniciada desde Memoria Estática. Conectando telemetría...</div>
    </div>
    <div id="input-panel">
        <div id="voice-indicator" title="Núcleo de Voz Pasiva"></div>
        <span style="color: var(--neon-blue); font-weight: bold;">>&nbsp;</span>
        <input type="text" id="input-command" placeholder="Inyectar secuencia de comandos..." autocomplete="off">
        <button class="action-btn" onclick="triggerUpload()">INYECTAR_MEDIO</button>
        <button class="action-btn" onclick="enviarComando()">EJECUTAR</button>
    </div>
    <input type="file" id="hidden-file-input" accept="image/*,.pdf,.txt,.py,.log,.js,.json" onchange="ejecutarUpload(this)">
    <audio id="audio-player" style="display: none;"></audio>

    <script>
        const consoleContainer = document.getElementById('console-container');
        const inputCommand = document.getElementById('input-command');
        const audioPlayer = document.getElementById('audio-player');
        const voiceIndicator = document.getElementById('voice-indicator');
        const systemStatus = document.getElementById('system-status');

        inputCommand.addEventListener('keypress', (e) => { if (e.key === 'Enter') enviarComando(); });

        const telemetrySource = new EventSource('/stream_telemetria');
        telemetrySource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                imprimirLog(data.origen, data.mensaje || data.texto);
            } catch(e) {}
        };

        async function enviarComando(textoDictado = null) {
            const cmd = textoDictado ? textoDictado.trim() : inputCommand.value.trim();
            if (!cmd) return;
            if (!textoDictado) inputCommand.value = '';
            imprimirLog('USER', cmd);

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: 'ennio', message: cmd })
                });
                const data = await response.json();
                const msgTexto = data.text || data.mensaje || JSON.stringify(data);
                imprimirLog('TERCERO', msgTexto);
            } catch (err) {
                imprimirLog('CRITICAL', 'CRITICAL ERROR: Fallo de enlace con el servidor.');
            }
        }

        function triggerUpload() { document.getElementById('hidden-file-input').click(); }
        async function ejecutarUpload(input) {
            if (!input.files || input.files.length === 0) return;
            const file = input.files[0];
            imprimirLog('SYSTEM', `Cargando archivo: ${file.name}`);
            const formData = new FormData();
            formData.append('user_id', 'ennio');
            formData.append('file', file);
            try {
                const response = await fetch('/upload', { method: 'POST', body: formData });
                const data = await response.json();
                imprimirLog('TERCERO', data.text || data.mensaje || JSON.stringify(data));
            } catch (err) {
                imprimirLog('CRITICAL', 'CRITICAL ERROR: Inyección multimedia fallida.');
            }
            input.value = '';
        }

        function imprimirLog(origen, texto) {
            const entry = document.createElement('div');
            entry.classList.add('log-entry');
            if (origen === 'USER') { entry.classList.add('user-log'); entry.innerHTML = `[ENNIO]: ${texto}`; }
            else if (origen === 'TERCERO') { entry.classList.add('tercero-log'); entry.innerHTML = `[TERCERO]: ${texto}`; }
            else if (origen === 'SYSTEM') { entry.classList.add('system-log'); entry.innerHTML = `[MAINFRAME]: ${texto}`; }
            else { entry.classList.add('critical-log'); entry.innerHTML = `[SISTEMA]: ${texto}`; }
            consoleContainer.appendChild(entry);
            consoleContainer.scrollTop = consoleContainer.scrollHeight;
            consoleContainer.stopPropagation;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.lang = 'es-VE';
            let modoEscuchaActiva = false;
            recognition.onstart = () => { systemStatus.innerHTML = "STATUS: CORE_ACTIVE | MIC: ESCUCHA_PASIVA"; };
            recognition.onresult = (event) => {
                const transcript = event.results[event.resultIndex][0].transcript.trim().toLowerCase();
                if (!modoEscuchaActiva) {
                    if (transcript.includes("tercero actívate") || transcript.includes("tercero activate")) {
                        modoEscuchaActiva = true;
                        voiceIndicator.classList.add('active');
                        systemStatus.innerHTML = "STATUS: CORE_ACTIVE | MIC: TRANSMITIENDO";
                        imprimirLog('SYSTEM', 'Matriz de voz activa iniciada...');
                    }
                } else {
                    enviarComando(transcript);
                    modoEscuchaActiva = false;
                    voiceIndicator.classList.remove('active');
                    systemStatus.innerHTML = "STATUS: CORE_ACTIVE | MIC: ESCUCHA_PASIVA";
                }
            };
            recognition.onerror = () => { try { recognition.start(); } catch(e){} };
            recognition.onend = () => { recognition.start(); };
            recognition.start();
        }
    </script>
</body>
</html>"""

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
# ENTORNO DE RUTAS DE LA API (RETORNO DIRECTO EN MEMORIA)
# =====================================================================

@flask_app.route('/')
def index():
    """Retorna la interfaz directamente desde memoria RAM evitando TemplateNotFound."""
    return Response(HTML_HUD, mimetype="text/html")

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

        ruta_guardado = os.path.join(core.files_dir, file.filename)
        file.save(ruta_guardado)
        
        respuesta_mainframe = core.procesar_archivo(user_id, ruta_guardado)
        return jsonify(respuesta_mainframe)
    except Exception as e:
        return jsonify({"error": f"Fallo en inyección multimedia: {str(e)}"}), 500

@flask_app.route('/stream_telemetria')
def stream_telemetria():
    """Canal continuo SSE para logs en tiempo real sincronizados con el HUD."""
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
app = WSGIMiddleware(flask_app)

if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
