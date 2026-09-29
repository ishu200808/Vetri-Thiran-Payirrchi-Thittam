"""Thin wrapper around the Google Gen AI SDK that returns parsed JSON."""
from typing import Optional

from .config import GEMINI_API_KEY, GEMINI_MODEL
from .utils import extract_json

SYSTEM_PROMPT = (
    "You are PocketSmart AI, a budget-aware shopping and planning assistant for "
    "users in India. All prices are in Indian Rupees (INR). Stay within the "
    "budgets you are given. Prefer well-known, realistic products and vendors. "
    "Prices are estimates. Reply with valid JSON only - no prose, no markdown."
)


class GeminiError(RuntimeError):
    pass


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_MODEL
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _get(self):
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate_json(self, prompt: str, image_bytes: Optional[bytes] = None,
                      mime_type: str = "image/jpeg", retries: int = 1) -> dict:
        if not self.available:
            raise GeminiError("GEMINI_API_KEY is not set.")
        from google.genai import types

        contents = [prompt]
        if image_bytes:
            contents.insert(0, types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0.6,
        )
        last_err = None
        for _ in range(retries + 1):
            try:
                resp = self._get().models.generate_content(
                    model=self.model, contents=contents, config=config
                )
                return extract_json(resp.text)
            except Exception as e:  # network, quota, bad JSON...
                last_err = e
        raise GeminiError(f"Gemini request failed: {last_err}")
