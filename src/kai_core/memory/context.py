class ContextManager:
    def __init__(self, max_history_length: int):
        self.max_history_length = max_history_length
        self.history = []

    def get_formatted_context(self) -> str:
        if not self.history:
            return "[Noch kein Kontext vorhanden]"
        return "\n".join(self.history)

    def update(self, transcript: str, visual_update: str):
        if transcript.strip():
            self.history.append(f"User (Audio): {transcript.strip()}")
        if visual_update.strip():
            self.history.append(f"System (Video): {visual_update.strip()}")
        self._truncate()

    def append_ai_response(self, text: str):
        if text.strip():
            self.history.append(f"KI: {text.strip()}")
        self._truncate()

    def _truncate(self):
        if len(self.history) > self.max_history_length:
            self.history = self.history[-self.max_history_length :]
