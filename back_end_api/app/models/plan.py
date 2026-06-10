from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    price_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String(10), nullable=False, default="USD")
    max_posts_per_day = Column(Integer, nullable=False, default=2)
    description = Column(Text, nullable=True)

    subscriptions = relationship("Subscription", back_populates="plan", cascade="all, delete-orphan")
