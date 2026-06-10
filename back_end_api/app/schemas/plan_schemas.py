from pydantic import BaseModel
from typing import Optional


class PlanResponse(BaseModel):
    id: int
    name: str
    slug: str
    price_cents: int
    currency: str
    max_posts_per_day: int = 0
    credit_amount: int = 0
    description: Optional[str] = None

    class Config:
        from_attributes = True
