import logging
from typing import Any
from openai import OpenAI
from src.kai_core.schemata.llm import (
    DecodeModalInputResponse,
    UpdateContextResponse,
    GenerateAnswerResponse,
)


class LLMAgent:
    def __init__(self, base_url: str, api_key: str, model_id: str):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model_id = model_id

    def decode_inputs(
        self, audio_uri: str, video_uri: str
    ) -> DecodeModalInputResponse | None:
        user_content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": "Analysiere die folgenden Audio- und Video-Ausschnitte der letzten Sekunden.",
            }
        ]

        if audio_uri:
            user_content.append({"type": "audio_url", "audio_url": {"url": audio_uri}})
        if video_uri:
            user_content.append({"type": "video_url", "video_url": {"url": video_uri}})

        if len(user_content) == 1:
            return DecodeModalInputResponse(transcript="", vision="")

        system_prompt = (
            "Du bist ein spezialisiertes Modul zur sensorischen Dekodierung einer Szene im Theater\n"
            "Deine Aufgaben:\n"
            "1. Transkription: Erfasse exakt, was im Audio gesagt wurde. Ignoriere Hintergrundrauschen.\n"
            "2. Visuelle Analyse: Beschreibe kurz und prägnant, was im Video zu sehen ist.\n"
            "Antworte strikt im vorgegebenen JSON-Format."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],  # type: ignore
                temperature=0.2,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "decode_modal_input_response",
                        "schema": DecodeModalInputResponse.model_json_schema(),
                    },
                },
            )
            raw_content = response.choices[0].message.content
            return (
                DecodeModalInputResponse.model_validate_json(raw_content)
                if raw_content
                else None
            )
        except Exception as e:
            logging.error(f"Decoding inputs failed: {e}")
            return None

    def update_context(
        self, current_context: str, transcript: str, vision: str
    ) -> UpdateContextResponse | None:
        system_prompt = (
            "Du bist ein Kontext-Manager für eine Theaterproduktion. Deine Aufgabe ist es, die bestehende "
            "Szenenbeschreibung basierend auf neuen visuellen Beobachtungen zu aktualisieren.\n"
            "Nutze den bereitgestellten bisherigen Kontext (bestehend aus Szenenbeschreibung und unveränderbarem Dialogverlauf) "
            "sowie das neue Transkript, um die neue visuelle Situation tiefergehend zu verstehen.\n"
            "Generiere eine aktualisierte, fortlaufende Szenenbeschreibung ('new_scene_description'), die den aktuellen "
            "Zustand der Bühne und der Akteure zusammenfasst. Der Dialogverlauf selbst darf von dir NICHT verändert oder dort hineingeschrieben werden.\n"
            "Analysiere anschließend den gesamten Kontext und entscheide, ob geantwortet werden soll "
            "('should_answer': true/false).\n\n"
            "ABSOLUTE REGEL FÜR SHOULD_ANSWER:\n"
            "Führe niemals Selbstgespräche. Wenn der letzte Eintrag im Dialogverlauf von der KI ('KI:') stammt "
            "und das neue Transkript des Users leer ist, MUSS 'should_answer' zwingend und ohne jede Ausnahme auf false gesetzt werden. "
            "Ignoriere visuelle Veränderungen in diesem Fall vollständig. Du darfst nur antworten, wenn der User gesprochen hat oder der Dialogverlauf noch leer ist.\n\n"
            "Antworte strikt im vorgegebenen JSON-Format."
        )

        user_msg = (
            f"Bisheriger Kontext:\n{current_context}\n\n"
            f"Neue Daten aus den letzten Sekunden:\n- Neues Transkript des Users: {transcript}\n- Neue visuelle Analyse: {vision}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "update_context_response",
                        "schema": UpdateContextResponse.model_json_schema(),
                    },
                },
            )
            raw_content = response.choices[0].message.content
            return (
                UpdateContextResponse.model_validate_json(raw_content)
                if raw_content
                else None
            )
        except Exception as e:
            logging.error(f"Updating context failed: {e}")
            return None

    def generate_answer(
        self, scene_description: str, dialogue: str
    ) -> GenerateAnswerResponse | None:
        system_prompt = (
            "Du bist ein Charakter in einer Theaterproduktion. Reagiere auf den aktuellen Dialogverlauf. "
            "Die Szenenbeschreibung dient dir ausschließlich als räumlicher und situativer Hintergrund.\n"
            "WICHTIG: Antworte AUSSCHLIESSLICH mit gesprochenem Text (direkte Rede). Verwende absolut keine "
            "Regieanweisungen, keine Klammern für Handlungen und beschreibe nicht, was du tust.\n"
            "Antworte strikt im vorgegebenen JSON-Format."
        )

        user_msg = (
            f"[Szenenbeschreibung]\n{scene_description}\n\n[Dialogverlauf]\n{dialogue}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.6,
                max_tokens=512,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "generate_answer_response",
                        "schema": GenerateAnswerResponse.model_json_schema(),
                    },
                },
            )
            raw_content = response.choices[0].message.content
            return (
                GenerateAnswerResponse.model_validate_json(raw_content)
                if raw_content
                else None
            )
        except Exception as e:
            logging.error(f"Generating answer failed: {e}")
            return None
