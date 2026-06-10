import asyncio
import os

from dotenv import load_dotenv
from google import genai

from app.schemas.post_generation_schemas import PostCreate
from app.services.post_prompt_service import build_prompts_from_json

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
client = genai.Client()


def _is_retryable_google_error(error: Exception) -> bool:
    message = str(error)
    return "503 UNAVAILABLE" in message or "'status': 'UNAVAILABLE'" in message


async def call_gemini_api(post: PostCreate):
    posts_data = build_prompts_from_json(post)

    async def process_item(item):
        attempts = 3
        for attempt in range(attempts):
            try:
                response = await client.aio.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=item.content,
                )
                item.content = response.text
                return item
            except Exception as error:
                if attempt < attempts - 1 and _is_retryable_google_error(error):
                    await asyncio.sleep(1.5 * (attempt + 1))
                    continue
                print(f"Gemini error for {item.title}: {error}")
                item.content = f"AI_ERROR: {error}"
                return item

    return await asyncio.gather(*(process_item(item) for item in posts_data))
