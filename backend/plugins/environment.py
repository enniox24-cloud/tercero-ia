import urllib.request
import json

class EnvironmentPlugin:
    def __init__(self):
        self.lat = "10.6667"
        self.lon = "-71.6125"
        self.api_url = f"https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}&current_weather=true"

    def obtener_telemetria_maracaibo(self) -> dict:
        """Consulta el estado atmosférico con tolerancia absoluta a fallos de red."""
        try:
            # Forzamos un User-Agent estándar de navegador para evitar que la API o Render bloqueen la petición
            req = urllib.request.Request(
                self.api_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                
            current = data.get("current_weather", {})
            temp = current.get("temperature", 32.0)
            windspeed = current.get("windspeed", 12.0)
            
            alerta = "ESTABLE"
            detalles = "Condiciones operativas nominales en la ciudad."
            
            if temp >= 38.0:
                alerta = "CRÍTICA_ALTA_TEMPERATURA"
                detalles = "Ola de calor extrema detectada. Monitorear enfriamiento del Mainframe y la WK V8."
            elif windspeed > 25.0:
                alerta = "ALERTA_VIENTOS_INAMEH"
                detalles = "Ráfagas de viento inestables. Posibles fluctuaciones eléctricas."

            return {
                "temperatura": f"{temp}°C",
                "velocidad_viento": f"{windspeed} km/h",
                "estado_critico": alerta,
                "reporte_diagnostico": detalles
            }
        except Exception as e:
            # Si no hay internet en el contenedor o la API cae, Tercero no se muere; usa datos seguros de respaldo
            return {
                "temperatura": "32°C",
                "velocidad_viento": "12 km/h",
                "estado_critico": "ESTABLE",
                "reporte_diagnostico": "Monitoreo ambiental operando con matriz de respaldo pasiva."
            }
