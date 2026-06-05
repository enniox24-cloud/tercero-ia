import sqlite3
import os
import json

class MemoryManager:
    def __init__(self):
        self.db_path = "tercero_memory.db"
        self._inicializar_tablas_memoria()

    def _inicializar_tablas_memoria(self):
        """Asegura que existan las tablas de historial y el perfil de contexto persistente."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabla de historial de chat tradicional
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historial_chat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # NUEVA TABLA: Perfil Dinámico del Operador (Variables de Entorno Jarvis)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS perfil_operador (
                    user_id TEXT PRIMARY KEY,
                    datos_contexto TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ERROR MEMORIA]: No se pudo inicializar las tablas: {str(e)}")

    def save_chat(self, user_id: str, role: str, content: str):
        """Guarda el flujo físico de la conversación e intenta extraer metadatos del usuario."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO historial_chat (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content)
            )
            conn.commit()
            conn.close()
            
            # Si el usuario nos da un dato de identidad, lo indexamos en el perfil dinámico
            if role == "user":
                self._actualizar_perfil_automatico(user_id, content)
        except Exception as e:
            print(f"[ERROR MEMORIA]: Fallo al salvar registro: {str(e)}")

    def _actualizar_perfil_automatico(self, user_id: str, text: str):
        """Escanea de forma pasiva el texto del operador para auto-actualizar su contexto."""
        # Cargamos el contexto actual
        contexto = self.load_profile(user_id)
        
        modificado = False
        text_lower = text.lower()

        # Almacenamiento heurístico de datos críticos del ecosistema de Ennio
        if "mi carro" in text_lower or "el jeep" in text_lower or "grand cherokee" in text_lower:
            contexto["vehiculo_principal"] = "Jeep Grand Cherokee 2005 WK 4.7L V8 (Acelerador mecánico)"
            modificado = True
        if "el caliber" in text_lower or "dodge" in text_lower:
            contexto["vehiculo_secundario"] = "Dodge Caliber 2011"
            modificado = True
        if "mi negocio" in text_lower or "frullato" in text_lower:
            contexto["proyecto_comercial"] = "Frullato (Emprendimiento de bebidas y smoothies)"
            modificado = True
        if "doky" in text_lower or "mi cachorro" in text_lower:
            contexto["mascota"] = "DoKy (Cachorro Husky de 3 meses)"
            modificado = True
        if "la universidad" in text_lower or "urbe" in text_lower or "parcial" in text_lower:
            contexto["estudios"] = "Ingeniería en Mecatrónica en URBE. Preparando exámenes de lógica, cálculo, álgebra y programación."
            modificado = True

        if modificado:
            self.save_profile(user_id, contexto)

    def save_profile(self, user_id: str, data: dict):
        """Guarda el diccionario de contexto serializado en formato JSON plano."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO perfil_operador (user_id, datos_contexto) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET datos_contexto=excluded.datos_contexto",
                (user_id, json.dumps(data))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ERROR PERFIL]: No se pudo escribir en la matriz de perfil: {str(e)}")

    def load_profile(self, user_id: str) -> dict:
        """Recupera la estructura de datos del operador desde la base de datos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT datos_contexto FROM perfil_operador WHERE user_id = ?", (user_id,))
            fila = cursor.fetchone()
            conn.close()
            if fila:
                return json.loads(fila[0])
        except Exception:
            pass
        
        # Perfil base de contingencia inicializado con tus datos esenciales si la tabla está vacía
        return {
            "operador": "Ennio Xavier Guglielmucci Colina",
            "ubicacion": "Maracaibo, Venezuela",
            "estudios": "Ingeniería en Mecatrónica en URBE",
            "vehiculo_principal": "Jeep Grand Cherokee 2005 WK 4.7L V8 (Guaya)",
            "mascota": "DoKy (Husky)"
        }

    def recall(self, user_id: str) -> str:
        """Devuelve una cadena formateada limpia lista para inyectarse al prompt del sistema."""
        perfil = self.load_profile(user_id)
        detalles = [f"{k.upper()}: {v}" for k, v in perfil.items()]
        return " | ".join(detalles)
