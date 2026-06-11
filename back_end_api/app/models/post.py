from sqlalchemy import Column, BigInteger, String, Text, Enum, ForeignKey, DateTime, JSON, Numeric, Integer, func
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship
from app.db import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    prompt = Column(Text().with_variant(mysql.LONGTEXT(), "mysql"), nullable=True)
    content = Column(Text().with_variant(mysql.LONGTEXT(), "mysql"), nullable=True)
    outline_json = Column(JSON, nullable=True)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    credit_cost = Column(Numeric(12, 6), nullable=False, default=0)
    status = Column(Enum("draft", "generated", "published", "failed", name="post_status"), nullable=False, default="generated")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="posts")
    history = relationship("PostHistory", back_populates="post", cascade="all, delete-orphan")
