class ContextManager:
    def __init__(self, max_history_length: int):
        self.max_history_length = max_history_length
        self.dialogue_history: list[str] = []
        self.scene_description: str = "Die Szene hat gerade begonnen."

    def get_formatted_context(self) -> str:
        return (
            f"[Aktuelle Szenenbeschreibung]\n{self.scene_description}\n\n"
            f"[Dialogverlauf]\n{self.get_dialogue_string()}"
        )

    def get_dialogue_string(self) -> str:
        return (
            "\n".join(self.dialogue_history)
            if self.dialogue_history
            else "[Kein Dialog bisher]"
        )

    def append_user_transcript(self, transcript: str):
        cleaned = transcript.strip()
        if cleaned:
            self.dialogue_history.append(f"User: {cleaned}")
            self._truncate()

    def append_ai_response(self, answer: str):
        cleaned = answer.strip()
        if cleaned:
            self.dialogue_history.append(f"KI: {cleaned}")
            self._truncate()

    def set_scene_description(self, description: str):
        self.scene_description = description.strip()

    def _truncate(self):
        if len(self.dialogue_history) > self.max_history_length:
            self.dialogue_history = self.dialogue_history[-self.max_history_length :]
