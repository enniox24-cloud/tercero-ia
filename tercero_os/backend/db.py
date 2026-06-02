# backend/db.py
import sqlite3

# Tu conexión original intacta
conn = sqlite3.connect("tercero.db", check_same_thread=False)
cursor = conn.cursor()

# Actualizamos la tabla agregando user_id para mantener la consistencia con core.py
cursor.execute("""
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    user_input TEXT,
    response TEXT
)
""")
conn.commit()


# ==========================================
# FUNCIONES ACCESORIAS (Para uso del sistema)
# ==========================================

def guardar_historial(user_id: str, user_input: str, response: str):
    """
    Guarda de forma persistente la interacción en la base de datos local sqlite.
    """
    try:
        cursor.execute("""
            INSERT INTO memory (user_id, user_input, response)
            VALUES (?, ?, ?)
        """, (user_id, user_input, response))
        conn.commit()
    except Exception as e:
        print(f"Error al guardar en sqlite: {str(e)}")


def obtener_historial(user_id: str, limite: int = 20):
    """
    Recupera los últimos registros de conversación específicos de un usuario.
    """
    try:
        cursor.execute("""
            SELECT user_input, response FROM memory
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limite))
        # Los invertimos para que queden en orden cronológico correcto (del más viejo al más nuevo)
        return cursor.fetchall()[::-1]
    except Exception as e:
        print(f"Error al leer de sqlite: {str(e)}")
        return []