from app.services.post_prompt_service import build_prompts_from_json
from dotenv import load_dotenv
from google import genai
from app.schemas.post_generation_schemas import PostCreate
import asyncio 

load_dotenv() # Load environment variables from .env file
client = genai.Client()


def _is_retryable_google_error(error: Exception) -> bool:
    message = str(error)
    return "503 UNAVAILABLE" in message or "'status': 'UNAVAILABLE'" in message
#function call gemini-2.5-flash
async def call_gemini_api(post: PostCreate):
    posts_data = build_prompts_from_json(post)
    
    # Hàm con để xử lý từng item
    async def process_item(item):
     try: # Dùng client.aio để thực sự chạy bất đồng bộ
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash", # Kiểm tra lại version model nhé (thường là 2.0 hoặc 1.5)
            contents=item.content
        )
        item.content = response.text
        return item
     except Exception as e:
        print(f"Lỗi tại item {item.title}: {e}")
        item.content = f"Lỗi gọi AI: {str(e)}"
        return item # Trả về item gốc nếu có lỗi, hoặc bạn có thể đánh dấu lỗi ở đây
    
    # Chạy SONG SONG tất cả các request cùng lúc
    final_results = await asyncio.gather(*(process_item(item) for item in posts_data))
    
    return final_results
