from datetime import datetime
from sqlalchemy.orm import Session
from app.models.subscription import Subscription
from app.models.payment import Payment
from app.models.user import User
from app.models.plan import Plan


def get_active_subscription(db: Session, user_id: int) -> Subscription | None:
    return (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id)
        .filter(Subscription.status == "active")
        .order_by(Subscription.started_at.desc())
        .first()
    )


def create_subscription(db: Session, user: User, plan: Plan, expires_at: datetime | None = None) -> Subscription:
    subscription = Subscription(user_id=user.id, plan_id=plan.id, started_at=datetime.utcnow(), expires_at=expires_at, status="active")
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def create_payment(db: Session, user: User, amount_cents: int, provider: str = "manual", currency: str = "USD", subscription: Subscription = None) -> Payment:
    payment = Payment(
        user_id=user.id,
        provider=provider,
        amount_cents=amount_cents,
        currency=currency,
        status="completed",
        subscription_id=subscription.id if subscription else None,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment
