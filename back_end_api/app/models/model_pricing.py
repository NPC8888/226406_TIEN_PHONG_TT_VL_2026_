from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, func

from app.db import Base


class ModelPricing(Base):
    __tablename__ = "model_pricing"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_key = Column(String(120), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    input_price_per_1m = Column(Numeric(12, 6), nullable=False)
    output_price_per_1m = Column(Numeric(12, 6), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
