# backend/memory.py
import json
import os

class MemoryManager:

    def __init__(self):
        # Aseguramos que el archivo siempre esté en la raíz del proyecto
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.file = os.path.join(base_dir, "memory.json")

        if not os.path.exists(self.file) or os.path.getsize(self.file) == 0:
            with open(self.file, "w") as f:
                json.dump({}, f)

    def remember(self, user_id: str, key: str, value: str):
        try:
            with open(self.file, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}

        if user_id not in data:
            data[user_id] = {}

        data[user_id][key] = value

        with open(self.file, "w") as f:
            json.dump(data, f, indent=4)

    def recall(self, user_id: str) -> str:
        try:
            with open(self.file, "r") as f:
                data = json.load(f)
        except Exception:
            return "No hay datos clave registrados sobre el usuario todavía."

        user_data = data.get(user_id, {})

        if not user_data:
            return "No hay datos clave registrados sobre el usuario todavía."

        memory_text = ""
        for key, value in user_data.items():
            memory_text += f"- {key}: {value}\n"

        return memory_text.strip()