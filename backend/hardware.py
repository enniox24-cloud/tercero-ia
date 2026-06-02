# backend/hardware.py
import serial
import time
import platform
from serial.tools import list_ports

class HardwareBridge:
    def __init__(self, baudios=9600):
        self.baudios = baudios
        self.serial_com = None
        self.conectado = False
        self.puerto = None
        self.conectar()

    def buscar_puerto_arduino(self):
        """
        Escanea los puertos COM de Windows para detectar automáticamente 
        el chip CH340 o controladores Arduino oficiales.
        """
        puertos_disponibles = list(list_ports.comports())
        
        # 1. Intento por descripción o hardware conocido (CH340, Arduino, USB-Serial)
        for p in puertos_disponibles:
            desc = p.description.lower()
            hwid = p.hwid.lower()
            if "ch340" in desc or "arduino" in desc or "usb-serial" in desc or "ch340" in hwid:
                print(f"-> Microcontrolador detectado automáticamente en: {p.device} ({p.description})")
                return p.device
                
        # 2. Contingencia: Si no encuentra palabras clave, agarra el último puerto COM activo (excepto el COM1 de sistema)
        puertos_com = [p.device for p in puertos_disponibles if p.device != "COM1"]
        if puertos_com:
            print(f"-> Forzando conexión en el último puerto activo detectado: {puertos_com[-1]}")
            return puertos_com[-1]
            
        return None

    def conectar(self):
        if platform.system() != "Windows":
            print("Puente Serial abortado: Sistema operativo no es Windows.")
            return
            
        # Detectamos el puerto dinámicamente
        self.puerto = self.buscar_puerto_arduino()
        
        if not self.puerto:
            print("-> ERROR CRÍTICO: No se detectó ninguna placa Arduino conectada por USB.")
            self.conectado = False
            return

        try:
            # Inicializamos la conexión física serial con la placa
            self.serial_com = serial.Serial(self.puerto, self.baudios, timeout=1)
            time.sleep(2)  # Esperas del auto-reset del Arduino (Crucial para el CH340)
            self.conectado = True
            print(f"-> Puente mecatrónico acoplado con éxito en el puerto {self.puerto}.")
        except Exception as e:
            print(f"-> ERROR CRÍTICO: No se pudo abrir el bus serial en {self.puerto}. Detalles: {e}")
            self.conectado = False

    def enviar_comando(self, comando: str) -> str:
        if not self.conectado or not self.serial_com:
            return "Falla de enlace: El microcontrolador no está respondiendo en el puerto físico o no fue detectado."
            
        try:
            # Enviamos la cadena con el salto de línea que espera el firmware
            cadena_envio = f"{comando}\n"
            self.serial_com.write(cadena_envio.encode('utf-8'))
            
            # Leemos la confirmación que nos devuelve el Arduino
            respuesta_arduino = self.serial_com.readline().decode('utf-8').strip()
            
            if respuesta_arduino:
                return respuesta_arduino
            return "Comando enviado, esperando secuenciación de retorno."
        except Exception as e:
            return f"Error de transmisión en el bus serial: {str(e)}"

# Instanciamos el puente global que maneja automáticamente las solicitudes de backend/tools.py
bridge = HardwareBridge(baudios=9600)