from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from app.models.post import Post
from app.models.post_history import PostHistory


def _is_missing_outline_json_column(error: OperationalError) -> bool:
    message = str(error.orig) if getattr(error, "orig", None) is not None else str(error)
    return "Unknown column 'outline_json'" in message

def create_post(
    db: Session,
    user_id: int,
    title: str,
    prompt: str = None,
    content: str = None,
    outline_json=None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    credit_cost=0,
    status: str = "generated",
) -> Post:
    post = Post(
        user_id=user_id,
        title=title,
        prompt=prompt,
        content=content,
        outline_json=outline_json,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        credit_cost=credit_cost,
        status=status
    )
    db.add(post)
    try:
        db.commit()
    except OperationalError as error:
        db.rollback()
        if not _is_missing_outline_json_column(error):
            raise

        post = Post(
            user_id=user_id,
            title=title,
            prompt=prompt,
            content=content,
            status=status
        )
        db.add(post)
        db.commit()
    return post

def create_post_history(
    db: Session,
    post_id: int,
    user_id: int,
    title: str,
    prompt: str = None,
    content: str = None,
    outline_json=None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    credit_cost=0,
    status: str = "generated",
) -> PostHistory:
    history = PostHistory(
        post_id=post_id,
        user_id=user_id,
        title=title,
        prompt=prompt,
        content=content,
        outline_json=outline_json,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        credit_cost=credit_cost,
        status=status
    )
    db.add(history)
    try:
        db.commit()
    except OperationalError as error:
        db.rollback()
        if not _is_missing_outline_json_column(error):
            raise

        history = PostHistory(
            post_id=post_id,
            user_id=user_id,
            title=title,
            prompt=prompt,
            content=content,
            status=status
        )
        db.add(history)
        db.commit()
    return history
