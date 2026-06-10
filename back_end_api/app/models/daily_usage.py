from sqlalchemy import Column, BigInteger, Date, Integer, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.db import Base


class DailyUsage(Base):
    __tablename__ = "daily_usage"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    usage_date = Column(Date, nullable=False)
    posts_created = Column(Integer, nullable=False, default=0)
    updated_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="daily_usage")
