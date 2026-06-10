import os
from datetime import timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.user import get_current_user
from app.db import get_db
from app.models.model_pricing import ModelPricing
from app.models.payment import Payment
from app.models.post import Post
from app.models.user import User
from app.schemas.admin_schemas import AdminDashboardResponse, AdminLoginRequest, AdminTokenResponse, ModelPricingResponse, ModelPricingUpdate
from app.services.auth_service import create_access_token
from app.services.credit_service import DEFAULT_MODEL_KEY, MODEL_PRICING_DEFAULTS, get_model_pricing


router = APIRouter(prefix="/admin", tags=["admin"])

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@smomer.example.com")


def _float(value) -> float:
    return float(value or 0)


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
def get_admin_dashboard(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    for model_key in MODEL_PRICING_DEFAULTS:
        get_model_pricing(db, model_key)

    total_input_tokens = int(db.query(func.coalesce(func.sum(Post.input_tokens), 0)).scalar() or 0)
    total_output_tokens = int(db.query(func.coalesce(func.sum(Post.output_tokens), 0)).scalar() or 0)
    total_credit_spent = _float(db.query(func.coalesce(func.sum(Post.credit_cost), 0)).scalar())
    total_users = int(db.query(func.count(User.id)).scalar() or 0)
    total_posts = int(db.query(func.count(Post.id)).scalar() or 0)
    total_revenue_usd_cents = int(
        db.query(func.coalesce(func.sum(Payment.amount_cents), 0))
        .filter(Payment.status == "completed")
        .filter(Payment.currency == "USD")
        .scalar()
        or 0
    )
    total_revenue_vnd = int(
        db.query(func.coalesce(func.sum(Payment.amount_cents), 0))
        .filter(Payment.status == "completed")
        .filter(Payment.currency == "VND")
        .scalar()
        or 0
    )
    pending_revenue_vnd = int(
        db.query(func.coalesce(func.sum(Payment.amount_cents), 0))
        .filter(Payment.status == "pending")
        .filter(Payment.currency == "VND")
        .scalar()
        or 0
    )
    pending_payments = int(db.query(func.count(Payment.id)).filter(Payment.status == "pending").scalar() or 0)

    paid_by_user = dict(
        db.query(Payment.user_id, func.coalesce(func.sum(Payment.amount_cents), 0))
        .filter(Payment.status == "completed")
        .group_by(Payment.user_id)
        .all()
    )

    users = (
        db.query(User)
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
            "total_paid_usd": _float(Decimal(str(paid_by_user.get(user.id, 0))) / Decimal("100")),
            "created_at": user.created_at,
        }
        for user in users
    ]

    pricing = db.query(ModelPricing).order_by(ModelPricing.id.asc()).all()

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
        "model_pricing": pricing,
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
            for payment in db.query(Payment).order_by(Payment.created_at.desc()).limit(20).all()
        ],
    }


@router.get("/model-pricing", response_model=list[ModelPricingResponse])
def list_model_pricing(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    for model_key in MODEL_PRICING_DEFAULTS:
        get_model_pricing(db, model_key)
    return db.query(ModelPricing).order_by(ModelPricing.id.asc()).all()


@router.put("/model-pricing/{model_key}", response_model=ModelPricingResponse)
def update_model_pricing(
    model_key: str,
    payload: ModelPricingUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    pricing = get_model_pricing(db, model_key)
    pricing.display_name = payload.display_name
    pricing.input_price_per_1m = payload.input_price_per_1m
    pricing.output_price_per_1m = payload.output_price_per_1m
    pricing.active = payload.active
    db.commit()
    db.refresh(pricing)
    return pricing
