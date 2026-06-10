from sqlalchemy.orm import Session
from app.models.plan import Plan


def get_plan_by_slug(db: Session, slug: str) -> Plan | None:
    return db.query(Plan).filter(Plan.slug == slug).first()


def list_plans(db: Session) -> list[Plan]:
    return db.query(Plan).order_by(Plan.price_cents).all()
