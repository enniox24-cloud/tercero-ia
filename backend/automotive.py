import re

class AutomotiveDiagnostic:
    def __init__(self):
        # Base de conocimiento técnico para diagnóstico con multímetro
        self.knowledge_base = {
            "MAP": {
                "sensor": "Sensor MAP (Presión Absoluta del Múltiple)",
                "voltajes": "Alimentación: 5.0 V | Tierra: < 0.05 V | Señal en ralentí: ~1.0 V a 1.5 V | Llave en ON (motor apagado): ~4.5 V a 4.8 V",
                "procedimiento": [
                    "1. Inspección de Vacío: Verifica que las mangueras de vacío del múltiple de admisión no tengan fugas o grietas.",
                    "2. Prueba de Alimentación: Con la llave en ON (motor apagado) y el sensor desconectado, mide con el multímetro el pin de alimentación. Debe marcar 5V exactos.",
                    "3. Prueba de Tierra: Mide continuidad entre el pin de tierra del conector y el negativo de la batería (debe ser menor a 0.05V).",
                    "4. Prueba de Señal: Conecta el sensor, pincha el cable de señal y enciende el motor. Al acelerar a fondo brevemente, el voltaje de señal debe subir rápidamente hacia los 4.5V y caer suavemente al soltar el acelerador."
                ]
            },
            "IAT": {
                "sensor": "Sensor IAT (Temperatura del Aire de Admisión)",
                "voltajes": "Alimentación: 5.0 V (Línea de retorno de señal) | Resistencia típica a 25°C: ~10k a 12k Ohms",
                "procedimiento": [
                    "1. Inspección Física: Desmonta el sensor y verifica que el termistor no esté impregnado de aceite, carbón o suciedad.",
                    "2. Prueba de Voltaje de Referencia: Desconecta el sensor, pon la llave en ON y mide el conector del arnés. Debes registrar 5V de referencia enviados por la PCM.",
                    "3. Prueba de Resistencia (Multímetro en Ohms): Mide los dos pines del sensor desconectado. Aplica calor suave (con tus manos o un secador) y verifica que la resistencia baje de forma fluida (comportamiento NTC). Si marca circuito abierto (OL), reemplaza el sensor."
                ]
            }
        }

    def analizar_consulta(self, mensaje: str) -> str:
        """Escanea la consulta buscando códigos de error OBD-II o menciones a sensores."""
        mensaje_upper = mensaje.upper()
        
        # Mapeo de códigos OBD-II estándar a sus respectivos componentes
        codigos_obd = {
            r"\bP0107\b|\bP0108\b|\bP0109\b": "MAP",
            r"\bP0111\b|\bP0112\b|\bP0113\b": "IAT"
        }
        
        componente_detectado = None
        
        # 1. Búsqueda por código de falla exacto
        for patron, comp in codigos_obd.items():
            if re.search(patron, mensaje_upper):
                componente_detectado = comp
                break
                
        # 2. Búsqueda por nombre común del sensor si no hay código
        if not componente_detectado:
            if "MAP" in mensaje_upper or "PRESION ABSOLUTA" in mensaje_upper:
                componente_detectado = "MAP"
            elif "IAT" in mensaje_upper or "TEMPERATURA DE ADMISION" in mensaje_upper or "TEMPERATURA DEL AIRE" in mensaje_upper:
                componente_detectado = "IAT"
                
        # 3. Si se intercepta el componente, se genera la inyección técnica
        if componente_detectado:
            datos = self.knowledge_base[componente_detectado]
            pasos_formateados = "\n".join(datos["procedimiento"])
            
            return (
                f"\n\n[SISTEMA - PROTOCOLO DE DIAGNÓSTICO AUTOMOTRIZ ACTIVO]:\n"
                f"El operador reporta anomalías en el {datos['sensor']}.\n"
                f"Métricas nominales de referencia:\n- {datos['voltajes']}\n\n"
                f"Flujo de comprobación física con multímetro:\n{pasos_formateados}\n\n"
                f"Instrucción: Integra estos datos y guía a Ennio con autoridad técnica y de forma directa paso a paso."
            )
            
        return ""
