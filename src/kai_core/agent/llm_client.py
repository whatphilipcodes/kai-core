import logging
from typing import Any
from openai import OpenAI
from src.kai_core.schemata.llm import ContextUpdateResponse


class LLMAgent:
    def __init__(self, base_url: str, api_key: str, model_id: str):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model_id = model_id

        self.system_prompt = (
            "Du bist ein multimodales KI-System. \n"
            "Dir werden der bisherige Text-Kontext der Konversation sowie ein neuer Audio- "
            "und Video-Ausschnitt der letzten Sekunden übergeben.\n\n"
            "Deine Aufgaben:\n"
            "1. Transkription: Erfasse exakt, was im neuen Audio gesagt wurde. Ignoriere Hintergrundrauschen. "
            "Wenn ein Wort oder Satz aufgrund des Zeitfensters abgeschnitten ist, transkribiere den Teilbruch exakt so, wie er hörbar ist.\n"
            "2. Visuelle Analyse: Beschreibe kurz, ob sich die visuelle Situation im Video maßgeblich verändert hat.\n"
            "3. Entscheidungslogik: Analysiere den Gesamtkontext. Entscheide, ob es Zeit ist zu antworten "
            "(z. B. weil eine Frage direkt an dich gestellt wurde oder eine deutliche Sprechpause nach einer abgeschlossenen Aussage entstanden ist).\n"
            "4. Antwort: Falls du antwortest, verfasse die Antwort auf Deutsch in direkter Rede.\n\n"
            "Du musst zwingend im geforderten JSON-Format antworten."
        )

    def query(
        self, text_context: str, audio_uri: str, video_uri: str
    ) -> ContextUpdateResponse | None:
        user_content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": "Hier sind die aktuellen Audio- und Video-Ausschnitte. Aktualisiere den Kontext und entscheide, ob du antworten musst.",
            }
        ]

        if audio_uri:
            user_content.append({"type": "audio_url", "audio_url": {"url": audio_uri}})
        if video_uri:
            user_content.append({"type": "video_url", "video_url": {"url": video_uri}})

        messages: list[Any] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f"Bisheriger Kontext:\n{text_context}"},
            {"role": "user", "content": user_content},
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,  # type: ignore
                temperature=0.4,
                max_tokens=1024,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "context_update_response",
                        "schema": ContextUpdateResponse.model_json_schema(),
                    },
                },
            )

            raw_content = response.choices[0].message.content
            if raw_content is None:
                return None

            return ContextUpdateResponse.model_validate_json(raw_content)

        except Exception as e:
            logging.error(f"LLM query failed: {e}")
            return None
