#endpoit post /generate-content
from json import dumps

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.post_generation_schemas import PostCreate, PostHistoryResponse
from app.services.gemini_service import call_gemini_api
from app.repositories.post_repository import create_post, create_post_history
from app.repositories.post_history_repository import get_post_history_by_user
from app.models.user import User
from app.services.auth_service import decode_access_token
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/generate-content")
async def generate_content(post: PostCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    list_response = await call_gemini_api(post)
    # Save to Post and PostHistory
    title = post.titles[0] if post.titles else "Generated Post"
    # Combine content from all generated posts
    content = "\n".join([f"<h2>{item.title}</h2>{item.content}" for item in list_response])
    prompt = f"Style: {post.style}, Sections: {[s.title for s in post.sections]}"
    
    new_post = create_post(db, current_user.id, title, prompt, content, "generated")
    create_post_history(db, new_post.id, current_user.id, title, prompt, content, "generated")
    
    # Return response in the format expected by frontend
    return {"message": "Bài viết đã được tạo thành công!", "data": [{"title": item.title, "content": item.content} for item in list_response]}

@router.get("/posts/history", response_model=list[PostHistoryResponse])
async def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    history = get_post_history_by_user(db, current_user.id)
    return history
