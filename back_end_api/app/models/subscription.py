from sqlalchemy import Column, Enum, ForeignKey, DateTime, BigInteger, func
from sqlalchemy.orm import relationship
from app.db import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    plan_id = Column(ForeignKey("plans.id"), nullable=False)
    started_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    status = Column(Enum("active", "cancelled", "expired", "past_due", name="subscription_status"), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")
