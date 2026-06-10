from sqlalchemy import Boolean, Column, Enum, String, BigInteger, TIMESTAMP, Numeric, Integer, func
from sqlalchemy.orm import relationship
from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=True)
    avatar_url = Column(String(1024), nullable=True)
    password_hash = Column(String(255), nullable=True)
    google_id = Column(String(255), nullable=True, unique=True)
    role = Column(Enum("user", "admin", name="user_role"), nullable=False, default="user")
    active = Column(Boolean, nullable=False, default=True)
    credit_balance = Column(Numeric(12, 6), nullable=False, default=1)
    total_input_tokens = Column(Integer, nullable=False, default=0)
    total_output_tokens = Column(Integer, nullable=False, default=0)
    total_credit_spent = Column(Numeric(12, 6), nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="user", cascade="all, delete-orphan")
    daily_usage = relationship("DailyUsage", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
