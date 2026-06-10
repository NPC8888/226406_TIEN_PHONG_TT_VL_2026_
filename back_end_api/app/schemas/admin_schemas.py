from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AdminMetricResponse(BaseModel):
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_users: int
    total_revenue_usd: float
    total_revenue_vnd: int = 0
    pending_revenue_vnd: int = 0
    pending_payments: int = 0
    total_credit_spent: float
    total_posts: int


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminUserInfo(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    role: str
    active: bool
    credit_balance: float
    total_input_tokens: int
    total_output_tokens: int
    total_credit_spent: float
    total_paid_usd: float
    created_at: datetime


class ModelPricingResponse(BaseModel):
    id: int
    model_key: str
    display_name: str
    input_price_per_1m: float
    output_price_per_1m: float
    active: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class ModelPricingUpdate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
    input_price_per_1m: float = Field(..., ge=0)
    output_price_per_1m: float = Field(..., ge=0)
    active: bool = True


class AdminPaymentInfo(BaseModel):
    id: int
    user_id: int
    user_email: str | None = None
    provider: str
    provider_payment_id: str | None = None
    amount: int
    currency: str
    status: str
    credit_amount: int = 0
    created_at: datetime
    updated_at: datetime


class AdminDashboardResponse(BaseModel):
    metrics: AdminMetricResponse
    users: list[AdminUserInfo]
    model_pricing: list[ModelPricingResponse]
    recent_payments: list[AdminPaymentInfo] = []
