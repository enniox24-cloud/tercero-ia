import math

class AlphaSimulator:
    def __init__(self):
        # Banco de datos de fórmulas inmutables para Mecatrónica e Ingeniería
        self.formulario_maestro = {
            "circuitos": {
                "ley_ohm": "V = I * R",
                "divisor_voltaje": "Vout = Vin * (R2 / (R1 + R2))",
                "potencia": "P = V * I"
            },
            "control": {
                "funcion_transferencia_primer_orden": "G(s) = K / (T*s + 1)",
                "p_i_d": "u(t) = Kp*e(t) + Ki*integral(e(t)) + Kd*(de/dt)"
            },
            "mecanica": {
                "torque": "T = F * r * sin(theta)",
                "potencia_rotacional": "P = T * omega"
            }
        }

    def simular_divisor_voltaje(self, vin: float, r1: float, r2: float) -> dict:
        """Calcula de forma exacta la caída de tensión en un nodo de control."""
        try:
            if (r1 + r2) == 0:
                return {"error": "Resistencia total no puede ser cero."}
            vout = vin * (r2 / (r1 + r2))
            return {
                "formula_usada": self.formulario_maestro["circuitos"]["divisor_voltaje"],
                "resultado_vout": round(vout, 4),
                "unidad": "Voltios (V)"
            }
        except Exception as e:
            return {"error": str(e)}

    def consultar_formulario(self, area: str) -> dict:
        """Devuelve las ecuaciones de un bloque específico para inyección en el prompt."""
        return self.formulario_maestro.get(area.lower(), {"info": "Área de ingeniería no indexada."})
