from sqlalchemy.orm import Session
from app.models.post_history import PostHistory
from typing import List

def get_post_history_by_user(db: Session, user_id: int) -> List[PostHistory]:
    return db.query(PostHistory).filter(PostHistory.user_id == user_id).order_by(PostHistory.changed_at.desc()).all()

def create_post_history(db: Session, post_history: PostHistory) -> PostHistory:
    db.add(post_history)
    db.commit()
    db.refresh(post_history)
    return post_history