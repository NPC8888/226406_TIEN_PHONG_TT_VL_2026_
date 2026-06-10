from sqlalchemy import Column, BigInteger, ForeignKey, String, Integer, Enum, JSON, DateTime, func
from sqlalchemy.orm import relationship
from app.db import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    subscription_id = Column(ForeignKey("subscriptions.id"), nullable=True)
    provider = Column(String(100), nullable=False)
    provider_payment_id = Column(String(255), nullable=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    status = Column(Enum("pending", "completed", "failed", "refunded", name="payment_status"), nullable=False, default="pending")
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")
