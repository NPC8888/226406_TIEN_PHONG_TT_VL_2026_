from __future__ import annotations

from decimal import Decimal, ROUND_UP

from sqlalchemy.orm import Session

from app.models.model_pricing import ModelPricing
from app.models.payment import Payment
from app.models.user import User
from app.schemas.post_generation_schemas import PostCreate


TOKEN_PRICE_DIVISOR = Decimal("1000000")
CREDIT_PACKAGES = (1, 5, 10, 50, 100)
DEFAULT_MODEL_KEY = "default"
MODEL_PRICING_DEFAULTS = {
    DEFAULT_MODEL_KEY: {
        "display_name": "Giá model đang dùng",
        "input_price_per_1m": Decimal("0.10"),
        "output_price_per_1m": Decimal("0.40"),
    },
}


def _decimal(value) -> Decimal:
    return Decimal(str(value or 0))


def get_model_pricing(db: Session, model_key: str | None = None) -> ModelPricing:
    key = DEFAULT_MODEL_KEY
    pricing = db.query(ModelPricing).filter(ModelPricing.model_key == key).first()
    if pricing is not None:
        return pricing

    legacy_pricing = db.query(ModelPricing).order_by(ModelPricing.id.asc()).first()
    defaults = MODEL_PRICING_DEFAULTS[DEFAULT_MODEL_KEY]
    pricing = ModelPricing(
        model_key=key,
        display_name=defaults["display_name"],
        input_price_per_1m=_decimal(legacy_pricing.input_price_per_1m) if legacy_pricing else defaults["input_price_per_1m"],
        output_price_per_1m=_decimal(legacy_pricing.output_price_per_1m) if legacy_pricing else defaults["output_price_per_1m"],
        active=True,
    )
    db.add(pricing)
    db.commit()
    db.refresh(pricing)
    return pricing


def calculate_credit_cost(input_tokens: int, output_tokens: int, pricing: ModelPricing | None = None) -> Decimal:
    default_pricing = MODEL_PRICING_DEFAULTS[DEFAULT_MODEL_KEY]
    input_price = _decimal(pricing.input_price_per_1m) if pricing is not None else default_pricing["input_price_per_1m"]
    output_price = _decimal(pricing.output_price_per_1m) if pricing is not None else default_pricing["output_price_per_1m"]
    cost = (
        Decimal(max(0, input_tokens)) * input_price
        + Decimal(max(0, output_tokens)) * output_price
    ) / TOKEN_PRICE_DIVISOR
    return cost.quantize(Decimal("0.000001"), rounding=ROUND_UP)


def estimate_generation_usage(post: PostCreate, db: Session | None = None) -> dict:
    titles = [title for title in post.titles if isinstance(title, str) and title.strip()]
    section_words = sum(max(0, int(section.word_count or 0)) for section in post.sections)
    title_chars = sum(len(title) for title in titles)
    section_chars = sum(len(section.title) + len(section.role) + len(section.description) for section in post.sections)
    style_chars = len(post.style or "")

    template_input_tokens = max(200, int((style_chars + section_chars + title_chars + 1800) / 3.5))
    article_input_tokens = max(250, int((style_chars + section_chars + 1200) / 3.5)) * max(1, len(titles))
    estimated_input_tokens = template_input_tokens + article_input_tokens

    estimated_output_tokens = max(1, len(titles)) * max(300, int(section_words * 1.7))
    pricing = get_model_pricing(db) if db is not None else None
    estimated_credit_cost = calculate_credit_cost(estimated_input_tokens, estimated_output_tokens, pricing)

    return {
        "input_tokens": estimated_input_tokens,
        "output_tokens": estimated_output_tokens,
        "total_tokens": estimated_input_tokens + estimated_output_tokens,
        "credit_cost": estimated_credit_cost,
        "model": post.ai_model,
        "input_price_per_1m": float(_decimal(pricing.input_price_per_1m)) if pricing is not None else float(MODEL_PRICING_DEFAULTS[DEFAULT_MODEL_KEY]["input_price_per_1m"]),
        "output_price_per_1m": float(_decimal(pricing.output_price_per_1m)) if pricing is not None else float(MODEL_PRICING_DEFAULTS[DEFAULT_MODEL_KEY]["output_price_per_1m"]),
    }


def get_credit_balance(user: User) -> Decimal:
    return _decimal(user.credit_balance)


def ensure_sufficient_credits(user: User, required_credits: Decimal) -> None:
    if get_credit_balance(user) < required_credits:
        raise ValueError("Insufficient credits")


def add_credits(db: Session, user: User, credits: int) -> User:
    if credits not in CREDIT_PACKAGES:
        raise ValueError("Invalid credit package")
    user.credit_balance = get_credit_balance(user) + Decimal(credits)
    payment = Payment(
        user_id=user.id,
        provider="manual_credit",
        amount_cents=credits * 100,
        currency="USD",
        status="completed",
        metadata_json={"credit_amount": credits},
    )
    db.add(payment)
    db.commit()
    db.refresh(user)
    return user


def apply_paid_credits(db: Session, user: User, credits: int) -> User:
    if credits <= 0:
        raise ValueError("Invalid credit amount")
    user.credit_balance = get_credit_balance(user) + Decimal(credits)
    db.commit()
    db.refresh(user)
    return user


def deduct_generation_credits(db: Session, user: User, input_tokens: int, output_tokens: int, model_key: str | None = None) -> Decimal:
    pricing = get_model_pricing(db)
    cost = calculate_credit_cost(input_tokens, output_tokens, pricing)
    user.credit_balance = max(Decimal("0"), get_credit_balance(user) - cost)
    user.total_input_tokens = int(user.total_input_tokens or 0) + int(input_tokens or 0)
    user.total_output_tokens = int(user.total_output_tokens or 0) + int(output_tokens or 0)
    user.total_credit_spent = _decimal(user.total_credit_spent) + cost
    db.commit()
    db.refresh(user)
    return cost
