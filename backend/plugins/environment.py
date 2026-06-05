import urllib.request
import json

class EnvironmentPlugin:
    def __init__(self):
        # Coordenadas estratégicas de Maracaibo, Venezuela
        self.lat = "10.6667"
        self.lon = "-71.6125"
        # Usamos una API meteorológica pública, gratuita y que no requiere llaves complejas
        self.api_url = f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&current_weather=true"

    def obtener_telemetria_maracaibo(self) -> dict:
        """Consulta en tiempo real el estado atmosférico de la zona de operaciones."""
        try:
            req = urllib.request.Request(self.api_url, headers={'User-Agent': 'TerceroOS-Mainframe'})
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode())
                
            current = data.get("current_weather", {})
            temp = current.get("temperature", 32.0)
            windspeed = current.get("windspeed", 0.0)
            
            # Heurística de alertas adaptada al entorno local
            alerta = "ESTABLE"
            detalles = "Condiciones operativas nominales en la ciudad."
            
            if temp >= 38.0:
                alerta = "CRÍTICA_ALTA_TEMPERATURA"
                detalles = "Ola de calor extrema detectada. Monitorear sistema de enfriamiento del Mainframe y presión de refrigerante en la WK V8."
            elif windspeed > 25.0:
                alerta = "ALERTA_VIENTOS_INAMEH"
                detalles = "Ráfagas de viento inestables de fondo. Posibles fluctuaciones en la red eléctrica local."

            return {
                "temperatura": f"{temp}°C",
                "velocidad_viento": f"{windspeed} km/h",
                "estado_critico": alerta,
                "reporte_diagnostico": detalles
            }
        except Exception as e:
            # Fallback pasivo en caso de fallos de conectividad internacional
            return {
                "temperatura": "N/D",
                "velocidad_viento": "N/D",
                "estado_critico": "MODO_RESILIENCIA",
                "reporte_diagnostico": f"Enlace ambiental temporalmente aislado: {str(e)}"
            }
