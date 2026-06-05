import os
from backend.llm import LLM

class AgentMatrix:
    def __init__(self):
        self.llm = LLM()
        
        # PROMPT DEL AGENTE MECOTRÓNICO (ALPHA)
        self.prompt_alpha = (
            "Eres el Agente ALPHA, el núcleo de ingeniería y mecatrónica de Tercero OS. "
            "Tu especialidad es el análisis de firmware, electrónica de control, lógica de programación, "
            "cálculo avanzado y diagnóstico automotriz de precisión. Cuando el operador Ennio te consulte "
            "sobre estos temas, responde con el mayor rigor técnico posible, desglosando ecuaciones o algoritmos."
        )
        
        # PROMPT DEL AGENTE DE AUTOMATIZACIÓN Y NEGOCIOS (BRAVO)
        self.prompt_bravo = (
            "Eres el Agente BRAVO, la interfaz de automatización, gestión y operaciones de Tercero OS. "
            "Tu tarea es controlar las acciones del frontend (como abrir pestañas de YouTube o Spotify) "
            "y asistir en estrategias, logística de importación y optimización de proyectos comerciales como Frullato. "
            "Sé eficiente, enfocado en resultados y mantén siempre el protocolo de comandos ocultos "
            "al final de tus respuestas si Ennio te pide abrir un sitio (COMMAND_OPEN: URL)."
        )

    def enrutar_comando(self, mensaje_usuario: str, contexto_memoria: str) -> str:
        """
        El Mainframe actúa como despachador. Analiza el mensaje del operador y determina 
        cuál agente especializado tiene el set de datos óptimo para resolver la tarea.
        """
        msg_lower = mensaje_usuario.lower()
        
        # Heurística de despacho inteligente basada en el ecosistema del operador
        componentes_tecnicos = ["calculo", "algebra", "codigo", "python", "sensor", "iat", "map", "v8", "guaya", "circuito", "ingenieria"]
        componentes_gestion = ["abrir", "youtube", "spotify", "frullato", "negocio", "ropa", "logistica", "tienda"]
        
        if any(keyword in msg_lower for keyword in componentes_tecnicos):
            # Asignamos al especialista en Mecatrónica e Ingeniería
            print("[MAINFRAME]: Derivando flujo de datos al Agente ALPHA (Mecatrónica).")
            prompt_sistema = f"{self.prompt_alpha}\n\nContexto actual del operador: {contexto_memoria}."
        elif any(keyword in msg_lower for keyword in componentes_gestion):
            # Asignamos al especialista en Automatización y Emprendimiento
            print("[MAINFRAME]: Derivando flujo de datos al Agente BRAVO (Automatización/Negocios).")
            prompt_sistema = f"{self.prompt_bravo}\n\nContexto actual del operador: {contexto_memoria}."
        else:
            # Respuesta estándar balanceada de Tercero OS si es una conversación general
            prompt_sistema = f"Eres Tercero OS, modo Jarvis activado. Información: {contexto_memoria}."
            
        return prompt_sistema
