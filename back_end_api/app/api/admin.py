import json
import os
from datetime import timedelta
from datetime import datetime, time
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from dotenv import dotenv_values, set_key
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.user import get_current_user
from app.db import get_db
from app.models.model_pricing import ModelPricing
from app.models.payment import Payment
from app.models.post import Post
from app.models.user import User
from app.schemas.admin_schemas import (
    AdminDashboardResponse,
    AdminEnvSettingsResponse,
    AdminEnvSettingsUpdateRequest,
    AdminEnvSettingsUpdateResponse,
    AdminGeminiTestRequest,
    AdminGeminiTestResponse,
    AdminLoginRequest,
    AdminPostDetailResponse,
    AdminTokenResponse,
    ModelPricingResponse,
    ModelPricingUpdate,
)
from app.services.auth_service import create_access_token
from app.services.credit_service import DEFAULT_MODEL_KEY, get_model_pricing


router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@smomer.example.com")
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
SECRET_MASK = "********"
ENV_CONFIG_FIELDS = [
    {
        "key": "AI_PROVIDER",
        "label": "Nguồn gọi Gemini",
        "description": "Vertex dùng file JSON service account, API key dùng key Gemini từ Google AI Studio.",
        "input_type": "select",
        "options": ["vertex_gemini", "gemini_api_key"],
        "requires_restart": True,
    },
    {
        "key": "GEMINI_API_KEY",
        "label": "Gemini API key",
        "description": "API key Gemini từ Google AI Studio. Để trống khi lưu nếu không muốn đổi.",
        "input_type": "password",
        "is_secret": True,
        "requires_restart": True,
    },
    {
        "key": "VERTEX_SERVICE_ACCOUNT_JSON",
        "label": "Vertex service account JSON",
        "description": "Dán nội dung JSON service account. Hệ thống sẽ lưu vào service-account.json.",
        "input_type": "textarea",
        "is_secret": True,
        "requires_restart": True,
    },
    {
        "key": "GEMINI_MODEL",
        "label": "Model Gemini",
        "description": "Model dùng chung cho tạo bài và gợi ý, áp dụng cho cả Vertex JSON và Gemini API key.",
        "input_type": "text",
        "requires_restart": True,
    },
]
ENV_CONFIG_BY_KEY = {item["key"]: item for item in ENV_CONFIG_FIELDS}


def _float(value) -> float:
    return float(value or 0)


def _read_env_values() -> dict:
    if not ENV_FILE.exists():
        return {}
    return dict(dotenv_values(ENV_FILE))


def _date_bounds(date_value: str | None = None, from_date: str | None = None, to_date: str | None = None):
    if date_value:
        day = datetime.fromisoformat(date_value).date()
        return datetime.combine(day, time.min), datetime.combine(day, time.max)
    start = datetime.combine(datetime.fromisoformat(from_date).date(), time.min) if from_date else None
    end = datetime.combine(datetime.fromisoformat(to_date).date(), time.max) if to_date else None
    return start, end


def _apply_date_filter(query, column, start, end):
    if start is not None:
        query = query.filter(column >= start)
    if end is not None:
        query = query.filter(column <= end)
    return query


def _post_detail_row(post: Post) -> dict:
    prompt_payload = {}
    if post.prompt:
        try:
            prompt_payload = json.loads(post.prompt)
        except json.JSONDecodeError:
            prompt_payload = {}
    diagnostics = prompt_payload.get("diagnostics") or []
    usage = prompt_payload.get("usage") or None
    llm_call_count = 0
    for item in diagnostics:
        details = item.get("details") if isinstance(item, dict) else {}
        calls = details.get("calls") if isinstance(details, dict) else None
        llm_call_count += len(calls or [])
    if not llm_call_count:
        llm_call_count = len(diagnostics)
    return {
        "id": post.id,
        "user_id": post.user_id,
        "user_email": post.user.email if post.user else None,
        "title": post.title,
        "status": post.status,
        "input_tokens": int(post.input_tokens or 0),
        "output_tokens": int(post.output_tokens or 0),
        "credit_cost": _float(post.credit_cost),
        "created_at": post.created_at,
        "content": post.content,
        "prompt": post.prompt,
        "ai_provider": prompt_payload.get("ai_provider"),
        "ai_model": prompt_payload.get("ai_model"),
        "llm_call_count": llm_call_count,
        "diagnostics": diagnostics,
        "usage": usage,
    }


def _env_item(field: dict, values: dict) -> dict:
    raw_value = values.get(field["key"], os.getenv(field["key"]))
    is_secret = bool(field.get("is_secret"))
    return {
        "key": field["key"],
        "label": field["label"],
        "description": field["description"],
        "value": SECRET_MASK if is_secret and raw_value else (raw_value or ""),
        "is_secret": is_secret,
        "input_type": field.get("input_type", "text"),
        "options": field.get("options"),
        "requires_restart": bool(field.get("requires_restart", True)),
    }


def _common_gemini_models() -> list[str]:
    return [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
    ]


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permission required")
    return current_user


def _get_or_create_default_admin(db: Session) -> User:
    admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
    legacy_admin = db.query(User).filter(User.email == "admin@smomer.local").first()
    if admin is None and legacy_admin is not None:
        legacy_admin.email = ADMIN_EMAIL
        admin = legacy_admin

    if admin is None:
        admin = User(
            email=ADMIN_EMAIL,
            name="Admin",
            role="admin",
            active=True,
            credit_balance=0,
            total_input_tokens=0,
            total_output_tokens=0,
            total_credit_spent=0,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin

    changed = False
    if admin.role != "admin":
        admin.role = "admin"
        changed = True
    if not admin.active:
        admin.active = True
        changed = True
    if changed:
        db.commit()
        db.refresh(admin)
    return admin


@router.post("/login", response_model=AdminTokenResponse)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Missing ADMIN_PASSWORD")
    if payload.username != ADMIN_USERNAME or payload.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sai tài khoản hoặc mật khẩu admin")

    admin = _get_or_create_default_admin(db)
    access_token = create_access_token(subject=str(admin.id), expires_delta=timedelta(hours=8))
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    date: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    current_pricing = get_model_pricing(db)
    try:
        start, end = _date_bounds(date, from_date, to_date)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Khoảng thời gian không hợp lệ")

    post_base = _apply_date_filter(db.query(Post), Post.created_at, start, end)
    payment_base = _apply_date_filter(db.query(Payment), Payment.created_at, start, end)
    user_base = _apply_date_filter(db.query(User), User.created_at, start, end)

    total_input_tokens = int(post_base.with_entities(func.coalesce(func.sum(Post.input_tokens), 0)).scalar() or 0)
    total_output_tokens = int(post_base.with_entities(func.coalesce(func.sum(Post.output_tokens), 0)).scalar() or 0)
    total_credit_spent = _float(post_base.with_entities(func.coalesce(func.sum(Post.credit_cost), 0)).scalar())
    total_users = int(user_base.with_entities(func.count(User.id)).scalar() or 0)
    total_posts = int(post_base.with_entities(func.count(Post.id)).scalar() or 0)
    total_revenue_usd_cents = int(
        payment_base.with_entities(func.coalesce(func.sum(Payment.amount_cents), 0))
        .filter(Payment.status == "completed")
        .filter(Payment.currency == "USD")
        .scalar()
        or 0
    )
    total_revenue_vnd = int(
        payment_base.with_entities(func.coalesce(func.sum(Payment.amount_cents), 0))
        .filter(Payment.status == "completed")
        .filter(Payment.currency == "VND")
        .scalar()
        or 0
    )
    pending_revenue_vnd = int(
        payment_base.with_entities(func.coalesce(func.sum(Payment.amount_cents), 0))
        .filter(Payment.status == "pending")
        .filter(Payment.currency == "VND")
        .scalar()
        or 0
    )
    pending_payments = int(payment_base.with_entities(func.count(Payment.id)).filter(Payment.status == "pending").scalar() or 0)

    paid_usd_by_user = dict(
        _apply_date_filter(db.query(Payment.user_id, func.coalesce(func.sum(Payment.amount_cents), 0)), Payment.created_at, start, end)
        .filter(Payment.status == "completed")
        .filter(Payment.currency == "USD")
        .group_by(Payment.user_id)
        .all()
    )
    paid_vnd_by_user = dict(
        _apply_date_filter(db.query(Payment.user_id, func.coalesce(func.sum(Payment.amount_cents), 0)), Payment.created_at, start, end)
        .filter(Payment.status == "completed")
        .filter(Payment.currency == "VND")
        .group_by(Payment.user_id)
        .all()
    )
    posts_by_user = dict(
        _apply_date_filter(db.query(Post.user_id, func.count(Post.id)), Post.created_at, start, end)
        .group_by(Post.user_id)
        .all()
    )

    users = (
        user_base
        .order_by(User.created_at.desc())
        .limit(200)
        .all()
    )
    user_rows = [
        {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "active": user.active,
            "credit_balance": _float(user.credit_balance),
            "total_input_tokens": int(user.total_input_tokens or 0),
            "total_output_tokens": int(user.total_output_tokens or 0),
            "total_credit_spent": _float(user.total_credit_spent),
            "total_posts": int(posts_by_user.get(user.id, 0) or 0),
            "total_paid_usd": _float(Decimal(str(paid_usd_by_user.get(user.id, 0))) / Decimal("100")),
            "total_paid_vnd": int(paid_vnd_by_user.get(user.id, 0) or 0),
            "created_at": user.created_at,
        }
        for user in users
    ]

    return {
        "metrics": {
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "total_users": total_users,
            "total_revenue_usd": total_revenue_usd_cents / 100,
            "total_revenue_vnd": total_revenue_vnd,
            "pending_revenue_vnd": pending_revenue_vnd,
            "pending_payments": pending_payments,
            "total_credit_spent": total_credit_spent,
            "total_posts": total_posts,
        },
        "users": user_rows,
        "model_pricing": [current_pricing],
        "recent_payments": [
            {
                "id": payment.id,
                "user_id": payment.user_id,
                "user_email": payment.user.email if payment.user else None,
                "provider": payment.provider,
                "provider_payment_id": payment.provider_payment_id,
                "amount": int(payment.amount_cents or 0),
                "currency": payment.currency,
                "status": payment.status,
                "credit_amount": int((payment.metadata_json or {}).get("credit_amount") or 0),
                "created_at": payment.created_at,
                "updated_at": payment.updated_at,
            }
            for payment in _apply_date_filter(db.query(Payment), Payment.created_at, start, end).order_by(Payment.created_at.desc()).limit(200).all()
        ],
        "recent_posts": [
            {
                "id": post.id,
                "user_id": post.user_id,
                "user_email": post.user.email if post.user else None,
                "title": post.title,
                "status": post.status,
                "input_tokens": int(post.input_tokens or 0),
                "output_tokens": int(post.output_tokens or 0),
                "credit_cost": _float(post.credit_cost),
                "created_at": post.created_at,
            }
            for post in post_base.order_by(Post.created_at.desc()).limit(200).all()
        ],
    }


@router.get("/model-pricing", response_model=list[ModelPricingResponse])
def list_model_pricing(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    return [get_model_pricing(db)]


@router.get("/env-settings", response_model=AdminEnvSettingsResponse)
def list_env_settings(_: User = Depends(require_admin)):
    values = _read_env_values()
    return {"items": [_env_item(field, values) for field in ENV_CONFIG_FIELDS]}


@router.put("/env-settings", response_model=AdminEnvSettingsUpdateResponse)
def update_env_settings(payload: AdminEnvSettingsUpdateRequest, _: User = Depends(require_admin)):
    ENV_FILE.touch(exist_ok=True)
    updated_keys = []
    requires_restart = False

    for item in payload.items:
        field = ENV_CONFIG_BY_KEY.get(item.key)
        if field is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Không cho phép sửa biến {item.key}")

        value = item.value.strip()
        if field.get("is_secret") and (not value or value == SECRET_MASK):
            continue

        if item.key == "VERTEX_SERVICE_ACCOUNT_JSON":
            try:
                json.loads(value)
            except json.JSONDecodeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service account JSON không hợp lệ")
            service_account_file = Path(__file__).resolve().parents[2] / "service-account.json"
            service_account_file.write_text(value, encoding="utf-8")
            set_key(str(ENV_FILE), "VERTEX_SERVICE_ACCOUNT_FILE", str(service_account_file))
            os.environ["VERTEX_SERVICE_ACCOUNT_FILE"] = str(service_account_file)
            updated_keys.append("VERTEX_SERVICE_ACCOUNT_FILE")
            requires_restart = True
            continue

        set_key(str(ENV_FILE), item.key, value)
        os.environ[item.key] = value
        updated_keys.append(item.key)
        requires_restart = requires_restart or bool(field.get("requires_restart", True))

    return {"updated_keys": updated_keys, "requires_restart": requires_restart}


@router.get("/posts/{post_id}", response_model=AdminPostDetailResponse)
def get_admin_post_detail(post_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bài viết")
    return _post_detail_row(post)


@router.post("/gemini/test-key", response_model=AdminGeminiTestResponse)
def test_gemini_key(payload: AdminGeminiTestRequest, _: User = Depends(require_admin)):
    provider = payload.provider or "gemini_api_key"
    model = payload.model or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash-lite"
    try:
        if provider == "gemini_api_key":
            from google import genai

            api_key = payload.api_key.strip()
            if not api_key or api_key == SECRET_MASK:
                raise ValueError("Chưa có Gemini API key để test")
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model=model, contents="Reply with OK.")
            models = []
            try:
                models = sorted(
                    {
                        item.name.removeprefix("models/")
                        for item in client.models.list()
                        if "gemini" in getattr(item, "name", "").lower()
                    }
                )
            except Exception:
                models = _common_gemini_models()
            return {"ok": True, "message": "API key hoạt động.", "models": models or _common_gemini_models()}

        if provider == "vertex_gemini":
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account

            raw_json = payload.service_account_json.strip()
            if raw_json and raw_json != SECRET_MASK:
                info = json.loads(raw_json)
                credentials = service_account.Credentials.from_service_account_info(
                    info,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"],
                )
            else:
                raise ValueError("Chưa có service account JSON để test")
            credentials.refresh(Request())
            return {"ok": True, "message": "Service account JSON hoạt động.", "models": _common_gemini_models()}

        raise ValueError("Provider không hợp lệ")
    except Exception as exc:
        return {"ok": False, "message": str(exc), "models": []}


@router.get("/gemini/models", response_model=AdminGeminiTestResponse)
def list_gemini_models(_: User = Depends(require_admin)):
    provider = os.getenv("AI_PROVIDER", "vertex_gemini")
    if provider == "gemini_api_key":
        return test_gemini_key(AdminGeminiTestRequest(provider=provider, api_key=os.getenv("GEMINI_API_KEY", "")), _)
    service_account_file = Path(os.getenv("VERTEX_SERVICE_ACCOUNT_FILE", str(Path(__file__).resolve().parents[2] / "service-account.json")))
    if not service_account_file.exists():
        return {"ok": False, "message": "Chưa có service account JSON để kiểm tra model.", "models": []}
    return {"ok": True, "message": "Service account JSON đã được cấu hình.", "models": _common_gemini_models()}


@router.put("/model-pricing/{model_key}", response_model=ModelPricingResponse)
def update_model_pricing(
    model_key: str,
    payload: ModelPricingUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    pricing = get_model_pricing(db)
    pricing.model_key = DEFAULT_MODEL_KEY
    pricing.display_name = "Giá model đang dùng"
    pricing.input_price_per_1m = payload.input_price_per_1m
    pricing.output_price_per_1m = payload.output_price_per_1m
    pricing.active = True
    db.commit()
    db.refresh(pricing)
    return pricing
