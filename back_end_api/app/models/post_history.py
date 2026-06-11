from sqlalchemy import Column, BigInteger, String, Text, Enum, ForeignKey, TIMESTAMP, JSON, Numeric, Integer, func
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import relationship
from app.db import Base


class PostHistory(Base):
    __tablename__ = "post_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    post_id = Column(ForeignKey("posts.id"), nullable=False)
    user_id = Column(ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    prompt = Column(Text().with_variant(mysql.LONGTEXT(), "mysql"), nullable=True)
    content = Column(Text().with_variant(mysql.LONGTEXT(), "mysql"), nullable=True)
    outline_json = Column(JSON, nullable=True)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    credit_cost = Column(Numeric(12, 6), nullable=False, default=0)
    status = Column(Enum("generated", "updated", "failed", name="post_history_status"), nullable=False)
    changed_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    post = relationship("Post", back_populates="history")
    user = relationship("User")
