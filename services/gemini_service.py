import json
import logging
from typing import Optional, Tuple
import httpx
from config import settings

logger = logging.getLogger("hand_ai.gemini")

SYSTEM_PROMPT = (
    "Read this handwritten note with extreme precision. Extract every single word, "
    "including margin notes, annotations, dates, bullet items, and mathematical notations. "
    "Maintain the layout and hierarchy using ONLY standard Markdown (# for headers, - for lists, "
    "** for emphasis, | for tables, ``` for code). DO NOT wrap in HTML tags. "
    "Output verbatim text with pristine Markdown formatting."
)

class GeminiService:
    @staticmethod
    async def extract_text_from_image(
        clean_base64_jpeg: str,
        language_hint: Optional[str] = "auto",
        custom_prompt: Optional[str] = None,
    ) -> Tuple[str, float, str]:
        """
        Calls Google Gemini Vision API to perform OCR on a preprocessed base64 JPEG image.
        Returns: (extracted_markdown_text, confidence_score, model_name).
        """
        api_key = settings.GEMINI_API_KEY.strip()
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured on the server. "
                "Please set GEMINI_API_KEY in hand_ai_api/.env or system environment."
            )

        prompt = custom_prompt or SYSTEM_PROMPT
        if language_hint and language_hint != "auto":
            prompt += f" The handwriting language is primarily: {language_hint}."

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": clean_base64_jpeg,
                            }
                        },
                        {"text": prompt},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,  # Low temperature for deterministic, factual transcription
                "maxOutputTokens": 8192,
            },
        }

        models_to_try = [settings.DEFAULT_MODEL] + [
            m for m in settings.FALLBACK_MODELS if m != settings.DEFAULT_MODEL
        ]

        last_error = ""

        async with httpx.AsyncClient(timeout=60.0) as client:
            for model in models_to_try:
                endpoint = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{model}:generateContent?key={api_key}"
                )

                try:
                    response = await client.post(
                        endpoint,
                        headers={"Content-Type": "application/json"},
                        json=payload,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts:
                                raw_text = parts[0].get("text", "")
                                return raw_text.strip(), 98.0, model

                    error_body = response.text
                    logger.warning(
                        f"Gemini API model {model} returned status {response.status_code}: {error_body}"
                    )

                    if response.status_code == 400 and "API_KEY_INVALID" in error_body:
                        raise ValueError("The server's Google Gemini API Key is invalid.")
                    elif response.status_code == 429:
                        last_error = "Gemini API rate limit or quota exceeded."
                        continue
                    elif response.status_code == 403:
                        raise PermissionError("Access forbidden by Gemini API. Check API key permissions.")

                    last_error = f"{model} returned HTTP {response.status_code}"

                except (httpx.ConnectError, httpx.TimeoutException) as exc:
                    logger.error(f"Network error connecting to Gemini ({model}): {exc}")
                    last_error = f"Network timeout contacting model {model}"
                    continue

            # ---------------------------------------------------------
            # Automatic Cross-Provider Fallback: Groq Vision (Qwen/Llama)
            # ---------------------------------------------------------
            groq_key = settings.GROQ_API_KEY.strip()
            if groq_key:
                logger.info("Attempting OCR fallback via Groq Vision API...")
                groq_model = settings.GROQ_MODEL
                groq_payload = {
                    "model": groq_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{clean_base64_jpeg}"
                                    },
                                },
                            ],
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4096,
                }

                try:
                    groq_res = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {groq_key}",
                            "Content-Type": "application/json",
                        },
                        json=groq_payload,
                        timeout=30.0,
                    )

                    if groq_res.status_code == 200:
                        groq_data = groq_res.json()
                        choices = groq_data.get("choices", [])
                        if choices:
                            message = choices[0].get("message", {})
                            content = message.get("content", "")
                            if content:
                                logger.info(f"Successfully processed OCR using Groq ({groq_model})")
                                return content.strip(), 96.0, f"groq/{groq_model}"
                    else:
                        logger.warning(
                            f"Groq API returned HTTP {groq_res.status_code}: {groq_res.text[:200]}"
                        )
                except Exception as groq_exc:
                    logger.warning(f"Error during Groq fallback: {groq_exc}")

        raise RuntimeError(f"All Vision models failed. Last error: {last_error}")
