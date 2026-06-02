# backend/tools.py
import os
import subprocess
import webbrowser
import psutil

def open_app(query: str) -> str:
    """
    Herramienta de automatización web y de aplicaciones.
    Permite a Tercero abrir lo que sea en Windows.
    """
    query_clean = query.lower().strip()
    
    # Mapeo de accesos rápidos para tu ecosistema de desarrollo y entretenimiento
    if "youtube" in query_clean:
        webbrowser.open("https://youtube.com")
        return "Abriendo YouTube en el navegador predeterminado, señor."
        
    elif "github" in query_clean:
        webbrowser.open("https://github.com")
        return "Accediendo a sus repositorios en GitHub."
        
    elif "arduino" in query_clean:
        # Intenta abrir el IDE de Arduino (ajusta la ruta si es necesario)
        try:
            subprocess.Popen(["cmd", "/c", "start", "arduino://"])
            return "Iniciando el entorno de desarrollo Arduino IDE."
        except:
            return "No se pudo lanzar Arduino automáticamente, pero el protocolo fue enviado."
            
    # Si le pides una web genérica (ej: "Abre google.com" o "Abre crocs.com")
    elif ".com" in query_clean or "http" in query_clean:
        url = query_clean.replace("abre", "").strip()
        if not url.startswith("http"):
            url = f"https://{url}"
        webbrowser.open(url)
        return f"Abriendo el sitio web {url} de inmediato."
        
    else:
        # Comando genérico de Windows: intenta abrir cualquier programa por su nombre
        try:
            programa = query_clean.replace("abre", "").strip()
            subprocess.Popen(["cmd", "/c", "start", programa])
            return f"Ejecutando orden de apertura para: {programa}."
        except Exception as e:
            return f"No encontré el ejecutable local para {query_clean}. Detalles: {str(e)}"

def system_status(query: str) -> str:
    """
    Módulo de diagnóstico de hardware. 
    Tercero analiza la salud de tu PC en tiempo real.
    """
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disco = psutil.disk_usage('C:\\').percent
    
    reporte = (
        f"Diagnóstico del Sistema de Cómputo:\n"
        f"- Carga del Procesador: {cpu}%\n"
        f"- Consumo de Memoria RAM: {ram}%\n"
        f"- Almacenamiento ocupado en Disco Principal (C:): {disco}%"
    )
    return reporte

def system_purge(query: str) -> str:
    """
    Módulo de mantenimiento. Purga archivos temporales y basura de Windows
    para optimizar el rendimiento del laboratorio.
    """
    try:
        # Ejecuta una limpieza rápida de temporales usando comandos de Windows
        os.system('del /q /f /s %TEMP%\\* >nul 2>&1')
        return "Purga de almacenamiento temporal completada. Rendimiento del sistema optimizado, señor."
    except Exception as e:
        return f"La purga falló debido a restricciones del sistema: {str(e)}"

def hardware_control(query: str) -> str:
    """
    Esta es la ranura de expansión mecatrónica (el relé).
    La dejamos lista para cuando decidas reactivar la placa física.
    """
    from backend.hardware import bridge
    if "encender" in query.lower() or "on" in query.lower():
        return bridge.enviar_comando("LED_ON")
    elif "apagar" in query.lower() or "off" in query.lower():
        return bridge.enviar_comando("LED_OFF")
    return "Comando de hardware no reconocido en la matriz."

def run_tool(tool_name: str, query: str) -> str:
    """
    Enrutador maestro. Conecta la decisión de la IA con la función de Windows.
    """
    mapa_herramientas = {
        "open_app": open_app,
        "system_status": system_status,
        "system_purge": system_purge,
        "hardware_control": hardware_control
    }
    
    if tool_name in mapa_herramientas:
        return mapa_herramientas[tool_name](query)
    return f"Error: La herramienta '{tool_name}' no está registrada en el núcleo de Tercero."