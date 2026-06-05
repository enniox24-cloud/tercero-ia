import sqlite3
import os
import json

class MemoryManager:
    def __init__(self):
        self.db_path = "tercero_memory.db"
        self.backup_path = "backup_context_operador.json"
        self._inicializar_tablas_memoria()
        self._verificar_y_restaurar_respaldo()

    def _inicializar_tablas_memoria(self):
        """Garantiza la creación del esquema lógico de almacenamiento local."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabla de historial lineal de interacciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS historial_chat (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabla de perfil persistente indexado
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS perfil_operador (
                    user_id TEXT PRIMARY KEY,
                    datos_contexto TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[CRÍTICO MEMORIA]: Fallo al estructurar tablas: {str(e)}")

    def _verificar_y_restaurar_respaldo(self):
        """Evita la amnesia de Render. Si la base de datos se borró, restaura el JSON."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM perfil_operador")
            if cursor.fetchone()[0] == 0 and os.path.exists(self.backup_path):
                print("[MEMORIA]: Detectado reinicio de Render. Inyectando respaldo de contexto...")
                with open(self.backup_path, 'r', encoding='utf-8') as f:
                    datos_json = f.read()
                cursor.execute(
                    "INSERT INTO perfil_operador (user_id, datos_contexto) VALUES (?, ?)",
                    ("ennio", datos_json)
                )
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"[REPARACIÓN]: No se pudo sincronizar el respaldo: {str(e)}")

    def save_chat(self, user_id: str, role: str, content: str):
        """Registra la conversación en curso y analiza variaciones de contexto."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO historial_chat (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content)
            )
            conn.commit()
            conn.close()
            
            if role == "user":
                self._actualizar_perfil_automatico(user_id, content)
        except Exception as e:
            print(f"[ERROR REGISTRO]: {str(e)}")

    def _actualizar_perfil_automatico(self, user_id: str, text: str):
        """Escáner pasivo heurístico para registrar cambios de entorno."""
        contexto = self.load_profile(user_id)
        modificado = False
        text_lower = text.lower()

        # Detección y refresco de variables del operador
        if "mi carro" in text_lower or "el jeep" in text_lower or "grand cherokee" in text_lower:
            contexto["vehiculo_principal"] = "Jeep Grand Cherokee 2005 WK 4.7L V8 (Acelerador mecánico por guaya)"
            modificado = True
        if "el caliber" in text_lower or "dodge" in text_lower:
            contexto["vehiculo_secundario"] = "Dodge Caliber 2011"
            modificado = True
        if "mi negocio" in text_lower or "frullato" in text_lower:
            contexto["proyecto_comercial"] = "Frullato (Emprendimiento físico de bebidas y smoothies)"
            modificado = True
        if "doky" in text_lower or "mi cachorro" in text_lower:
            contexto["mascota"] = "DoKy (Cachorro Husky de 3 meses)"
            modificado = True
        if "la universidad" in text_lower or "urbe" in text_lower or "parcial" in text_lower:
            contexto["estudios"] = "Ingeniería en Mecatrónica en URBE. Preparando evaluaciones de lógica, cálculo, álgebra y programación."
            modificado = True

        if modificado:
            self.save_profile(user_id, contexto)

    def save_profile(self, user_id: str, data: dict):
        """Escribe el contexto en la base de datos y genera copia espejo en disco."""
        try:
            str_datos = json.dumps(data, ensure_ascii=False, indent=4)
            
            # Guardado en base de datos
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO perfil_operador (user_id, datos_contexto) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET datos_contexto=excluded.datos_contexto",
                (user_id, str_datos)
            )
            conn.commit()
            conn.close()
            
            # Guardado en archivo espejo de contingencia
            with open(self.backup_path, 'w', encoding='utf-8') as f:
                f.write(str_datos)
        except Exception as e:
            print(f"[FALLO PERFIL]: {str(e)}")

    def load_profile(self, user_id: str) -> dict:
        """Extrae el perfil activo desde el almacenamiento de mayor disponibilidad."""
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

        if os.path.exists(self.backup_path):
            try:
                with open(self.backup_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Matriz base fija del ecosistema de Ennio
        return {
            "operador": "Ennio Xavier Guglielmucci Colina",
            "ubicacion": "Maracaibo, Venezuela",
            "estudios": "Ingeniería en Mecatrónica en URBE",
            "vehiculo_principal": "Jeep Grand Cherokee 2005 WK 4.7L V8 (Guaya)",
            "mascota": "DoKy (Husky)"
        }

    def calcular_simulacion_bravo(self, tipo_negocio: str, datos_financieros: dict) -> str:
        """Sub-módulo financiero de la matriz Enterprise: Ejecuta proyecciones de rentabilidad netas."""
        try:
            if tipo_negocio == "importacion":
                costo_origen = datos_financieros.get("costo_origen", 0)
                peso_libras = datos_financieros.get("peso_libras", 0)
                tarifa_flete = datos_financieros.get("tarifa_flete", 4.5) # Promedio Miami-Maracaibo puerta a puerta
                costo_nacionalizacion = datos_financieros.get("costo_nacionalizacion", 0)
                unidades = datos_financieros.get("unidades", 1)
                
                costo_flete_total = peso_libras * tarifa_flete
                costo_total_puesto = costo_origen + costo_flete_total + costo_nacionalizacion
                costo_unitario_real = costo_total_puesto / unidades
                
                return (
                    f"\n[MATRIZ LOGÍSTICA ENTERPRISE - REPORTE DE IMPORTACIÓN]:\n"
                    f"- Unidades Totales: {unidades}\n"
                    f"- Costo Flete Consolidado (Miami-Maracaibo): ${costo_flete_total:.2f}\n"
                    f"- Costo Total de Inversión Puesta en Destino: ${costo_total_puesto:.2f}\n"
                    f"- Costo Unitario Real de Despliegue por Pieza: ${costo_unitario_real:.2f}\n"
                    f"Sugerencia de Margen Operativo (35%): ${(costo_unitario_real * 1.35):.2f}"
                )
                
            elif tipo_negocio == "frullato":
                costo_materia_prima = datos_financieros.get("materia_prima", 0) # Frutas, bases, envases
                costos_fijos_proporcionales = datos_financieros.get("costos_fijos", 0) # Local, electricidad, personal por unidad
                precio_venta = datos_financieros.get("precio_venta", 0)
                
                costo_produccion_total = costo_materia_prima + costos_fijos_proporcionales
                margen_ganancia = precio_venta - costo_produccion_total
                porcentaje_margen = (margen_ganancia / precio_venta) * 100 if precio_venta > 0 else 0
                
                return (
                    f"\n[MATRIZ LOGÍSTICA ENTERPRISE - SIMULACIÓN RECEPTA FRULLATO]:\n"
                    f"- Costo de Producción Neto por Unidad: ${costo_produccion_total:.2f}\n"
                    f"- Margen Neto de Utilidad por Unidad Vendida: ${margen_ganancia:.2f}\n"
                    f"- Rendimiento Operativo de la Receta: {porcentaje_margen:.1f}%\n"
                    f"Estado Financiero: {'EFICIENTE_OPTIMIZADO' if porcentaje_margen >= 40 else 'REVISAR_PROPORCIONES_COSTO'}"
                )
        except Exception as e:
            return f"[ERROR CONSOLA FINANCIERA]: Fallo matemático: {str(e)}"
        return ""

    def recall(self, user_id: str) -> str:
        """Compila los metadatos planos para inyección directa en el prompt del sistema."""
        perfil = self.load_profile(user_id)
        detalles = [f"{k.upper()}: {v}" for k, v in perfil.items()]
        return " | ".join(detalles)
