from json import dumps
import unicodedata

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.repositories.post_history_repository import get_post_history_by_user
from app.repositories.post_repository import create_post, create_post_history
from app.schemas.post_generation_schemas import (
    GenerationEstimateResponse,
    PostCreate,
    PostHistoryResponse,
    SectionOutlineSuggestionRequest,
    SectionOutlineSuggestionResponse,
    WritingStyleSuggestionRequest,
    WritingStyleSuggestionResponse,
)
from app.services.credit_service import (
    deduct_generation_credits,
    ensure_sufficient_credits,
    estimate_generation_usage,
    get_credit_balance,
)
from app.services.auth_service import decode_access_token
from app.services.groq_service import call_ai_api, suggest_section_outlines, suggest_writing_styles
from app.services.vertex_gemini_service import call_vertex_gemini_api

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _normalize_unicode(text: str) -> str:
    """Normalize Unicode string to NFC form to fix Vietnamese character issues."""
    if not isinstance(text, str):
        return text
    return unicodedata.normalize("NFC", text)


def _is_ai_error(content: str) -> bool:
    return isinstance(content, str) and content.startswith("AI_ERROR:")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/generate-content")
async def generate_content(
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if post.ai_provider != "vertex_gemini":
        raise HTTPException(status_code=400, detail="Credit billing currently supports only Vertex Gemini models.")

    estimate = estimate_generation_usage(post, db)
    try:
        ensure_sufficient_credits(current_user, estimate["credit_cost"])
    except ValueError:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Không đủ credit. Dự đoán cần {float(estimate['credit_cost']):.6f} credit, "
                f"hiện có {float(get_credit_balance(current_user)):.6f} credit."
            ),
        )

    if post.ai_provider == "vertex_gemini":
        list_response = await call_vertex_gemini_api(post)
    else:
        list_response = await call_ai_api(post)
    failed_items = [item for item in list_response if _is_ai_error(item.content)]
    if failed_items and len(failed_items) == len(list_response):
        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily overloaded. Please try again in a moment.",
        )

    run_usage = {}
    if list_response and list_response[0].diagnostics:
        run_usage = list_response[0].diagnostics.get("run_usage") or {}
    input_tokens = int(run_usage.get("input_tokens") or estimate["input_tokens"])
    output_tokens = int(run_usage.get("output_tokens") or estimate["output_tokens"])
    credit_cost = deduct_generation_credits(db, current_user, input_tokens, output_tokens, post.ai_model)

    for item in failed_items:
        error_message = item.content.removeprefix("AI_ERROR:").strip()
        item.content = (
            "<article>"
            "<p><strong>Khong the tao noi dung luc nay.</strong></p>"
            f"<p>{_normalize_unicode(error_message)}</p>"
            "</article>"
        )

    title = post.titles[0] if post.titles else "Generated Post"
    title = _normalize_unicode(title)
    content = "\n".join([f"<h2>{_normalize_unicode(item.title)}</h2>{_normalize_unicode(item.content)}" for item in list_response])
    outline_json = [section.model_dump() for section in post.sections]
    prompt = dumps(
        {
            "style": post.style,
            "ai_provider": post.ai_provider,
            "ai_model": post.ai_model,
            "sections": outline_json,
            "template_plan": list_response[0].template_plan if list_response else None,
            "diagnostics": [{ "title": item.title, "details": item.diagnostics } for item in list_response],
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "credit_cost": float(credit_cost),
                "credit_balance_after": float(current_user.credit_balance or 0),
            },
        },
        ensure_ascii=False,
        indent=2,
    )

    new_post = create_post(
        db,
        current_user.id,
        title,
        prompt,
        content,
        outline_json,
        input_tokens,
        output_tokens,
        credit_cost,
        "generated",
    )
    create_post_history(
        db,
        new_post.id,
        current_user.id,
        title,
        prompt,
        content,
        outline_json,
        input_tokens,
        output_tokens,
        credit_cost,
        "generated",
    )

    return {
        "message": "Bai viet da duoc tao thanh cong!" if not failed_items else "Da tao bai viet, nhung mot so muc gap loi AI tam thoi.",
        "data": [{"title": _normalize_unicode(item.title), "content": _normalize_unicode(item.content)} for item in list_response],
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "credit_cost": float(credit_cost),
            "credit_balance": float(current_user.credit_balance or 0),
        },
    }


@router.post("/generate-content/estimate", response_model=GenerationEstimateResponse)
async def estimate_generate_content(
    post: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if post.ai_provider != "vertex_gemini":
        raise HTTPException(status_code=400, detail="Credit billing currently supports only Vertex Gemini models.")
    estimate = estimate_generation_usage(post, db)
    balance = get_credit_balance(current_user)
    return {
        "input_tokens": estimate["input_tokens"],
        "output_tokens": estimate["output_tokens"],
        "total_tokens": estimate["total_tokens"],
        "credit_cost": float(estimate["credit_cost"]),
        "credit_balance": float(balance),
        "has_enough_credits": balance >= estimate["credit_cost"],
        "model": estimate["model"],
    }


@router.post("/writing-style-suggestions", response_model=WritingStyleSuggestionResponse)
async def writing_style_suggestions(payload: WritingStyleSuggestionRequest):
    suggestions = await suggest_writing_styles(payload.titles)
    return {"suggestions": [_normalize_unicode(item) for item in suggestions]}


@router.post("/section-outline-suggestions", response_model=SectionOutlineSuggestionResponse)
async def section_outline_suggestions(payload: SectionOutlineSuggestionRequest):
    layouts = await suggest_section_outlines(payload.titles, payload.style, payload.description)
    return layouts if isinstance(layouts, dict) else {"layouts": layouts}


@router.get("/posts/history", response_model=list[PostHistoryResponse])
async def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_post_history_by_user(db, current_user.id)
