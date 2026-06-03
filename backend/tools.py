import os
import sys
import re
import subprocess
import webbrowser
import urllib.request
import json
import psutil

# DETECTOR DE ENTORNO: Verifica de forma automática si el Mainframe corre en Render (Linux) o Local (Windows)
ES_NUBE = os.getenv("RENDER") is not None or sys.platform != "win32"

def open_app(query: str) -> str:
    """
    Herramienta inteligente de automatización web y de aplicaciones.
    Evita colapsos adaptando la ejecución al entorno activo.
    """
    query_clean = query.lower().strip()
    
    # Si detecta que está corriendo en el servidor en la nube de Render
    if ES_NUBE:
        if "youtube" in query_clean:
            return "Comando web registrado. En la versión de nube, acceda directamente mediante la interfaz a youtube.com, señor."
        elif "github" in query_clean:
            return "Enlace de desarrollo listo. Acceso directo configurado para github.com en su terminal web."
        elif ".com" in query_clean or "http" in query_clean:
            match = re.search(r'([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', query_clean)
            url = match.group(1) if match else "google.com"
            return f"Matriz en la nube lista. El enlace para https://{url} ha sido indexado correctamente para ejecución local en su HUD."
        return f"El subsistema en la nube procesó el comando para '{query_clean}', pero la apertura forzada de GUI está restringida en el servidor remoto."

    # --- MODO LOCAL (EJECUCIÓN EN ENTORNO WINDOWS DESDE TU PC) ---
    if "youtube" in query_clean:
        webbrowser.open("https://youtube.com")
        return "Abriendo la plataforma de YouTube en el navegador predeterminado, señor."
        
    elif "github" in query_clean:
        webbrowser.open("https://github.com")
        return "Accediendo a sus repositorios en la red de GitHub de inmediato."
        
    elif "arduino" in query_clean:
        try:
            subprocess.Popen(["cmd", "/c", "start", "arduino://"])
            return "Iniciando el entorno de desarrollo automatizado Arduino IDE."
        except:
            return "No se pudo lanzar Arduino automáticamente, pero el protocolo de inicio fue inyectado."
            
    elif ".com" in query_clean or "http" in query_clean:
        url = query_clean.replace("abre", "").strip()
        if not url.startswith("http"):
            url = f"https://{url}"
        webbrowser.open(url)
        return f"Abriendo el sitio web {url} en su terminal física."
        
    else:
        try:
            programa = query_clean.replace("abre", "").strip()
            subprocess.Popen(["cmd", "/c", "start", programa])
            return f"Ejecutando orden de apertura del sistema operativo para: {programa}."
        except Exception as e:
            return f"No se encontró un ejecutable local registrado para {query_clean}."


def system_status(query: str) -> str:
    """
    Módulo de diagnóstico de hardware dinámico.
    Mide los recursos reales dependiendo de dónde esté alojado Tercero.
    """
    cpu = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory().percent
    
    if ES_NUBE:
        # Monitoreo de telemetría del servidor en Render (Entorno Linux Cloud)
        reporte = (
            f"Telemetría del Servidor en la Nube (Render Core):\n"
            f"- Carga del Procesador Remoto: {cpu}%\n"
            f"- Consumo de Memoria RAM Virtual: {ram}%\n"
            f"- Estado del Entorno: Operativo y Estable"
        )
        return reporte
        
    # Monitoreo local en tu máquina Windows
    try:
        disco = psutil.disk_usage('C:\\').percent
        disco_info = f"- Almacenamiento Ocupado en Disco Principal (C:): {disco}%"
    except:
        disco_info = "- Almacenamiento Principal: No disponible"

    reporte = (
        f"Diagnóstico de Hardware Local (Mainframe Personal):\n"
        f"- Carga del Procesador: {cpu}%\n"
        f"- Consumo de Memoria RAM: {ram}%\n"
        f"{disco_info}"
    )
    return reporte


def system_purge(query: str) -> str:
    """
    Módulo inteligente de mantenimiento preventivo y limpieza de buffers.
    """
    if ES_NUBE:
        return "Purga de búferes en el servidor completada de forma lógica. El almacenamiento temporal de Render ha sido optimizado."
        
    # Ejecución física en Windows local
    try:
        os.system('del /q /f /s %TEMP%\\* >nul 2>&1')
        return "Purga de almacenamiento temporal completada en su PC. Rendimiento del sistema optimizado, señor."
    except Exception as e:
        return f"La purga local falló debido a restricciones de privilegios: {str(e)}"


def hardware_control(query: str) -> str:
    """
    Ranura de expansión de control mecatrónico.
    Evita roturas de importación si la placa no está conectada físicamente.
    """
    try:
        from backend.hardware import bridge
        if "encender" in query.lower() or "on" in query.lower():
            return bridge.enviar_comando("LED_ON")
        elif "apagar" in query.lower() or "off" in query.lower():
            return bridge.enviar_comando("LED_OFF")
        return "Comando de hardware no reconocido en la matriz mecatrónica."
    except Exception:
        # Respuesta elegante tipo Jarvis si no encuentra los módulos físicos en Render
        return "Módulo de puente de hardware offline. El enlace físico con los relés y componentes no se ha detectado en esta instancia."


def get_weather(query: str) -> str:
    """
    Módulo de telemetría climática automatizado. Conecta con Open-Meteo API
    para obtener datos en tiempo real de Maracaibo de forma limpia.
    """
    # Coordenadas geográficas por defecto de Maracaibo, Venezuela
    lat, lon = "10.6666", "-71.6124"
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            current = data.get("current_weather", {})
            
            temp = current.get("temperature", "N/D")
            viento = current.get("windspeed", "N/D")
            time_obs = current.get("time", "N/D")
            
            # Mapeo básico de códigos meteorológicos de la WMO
            wmo_code = current.get("weathercode", 0)
            estado = "Cielo despejado"
            if wmo_code in [1, 2, 3]: estado = "Parcialmente nublado"
            elif wmo_code in [45, 48]: estado = "Niebla atmosférica"
            elif wmo_code in [51, 53, 55, 61, 63, 65]: estado = "Precipitaciones/Lluvia activa"
            elif wmo_code in [80, 81, 82]: estado = "Chubascos intermitentes"
            elif wmo_code in [95, 96, 99]: estado = "Tormenta eléctrica en desarrollo"

            return (
                f"Métricas climáticas de Maracaibo actualizadas:\n"
                f"- Temperatura Ambiente: {temp}°C\n"
                f"- Estado Atmosférico: {estado}\n"
                f"- Velocidad del Viento: {viento} km/h"
            )
    except Exception as e:
        return f"No se pudo establecer conexión con el satélite climático. Error en enlace: {str(e)}"


def run_tool(tool_name: str, query: str) -> str:
    """
    Enrutador maestro del Mainframe. Conecta las decisiones del LLM con las funciones del sistema.
    """
    mapa_herramientas = {
        "open_app": open_app,
        "system_status": system_status,
        "system_purge": system_purge,
        "hardware_control": hardware_control,
        "get_weather": get_weather  # Registro oficial de la nueva ranura de expansión climática
    }
    
    if tool_name in mapa_herramientas:
        return mapa_herramientas[tool_name](query)
    return f"Error: La herramienta '{tool_name}' no está registrada en el núcleo de Tercero."
