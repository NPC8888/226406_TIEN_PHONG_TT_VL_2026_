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
    total_posts: int = 0
    total_paid_usd: float
    total_paid_vnd: int = 0
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


class AdminEnvSettingInfo(BaseModel):
    key: str
    label: str
    description: str
    value: str | None = None
    is_secret: bool = False
    input_type: str = "text"
    options: list[str] | None = None
    requires_restart: bool = True


class AdminEnvSettingsResponse(BaseModel):
    items: list[AdminEnvSettingInfo]


class AdminEnvSettingUpdate(BaseModel):
    key: str
    value: str = ""


class AdminEnvSettingsUpdateRequest(BaseModel):
    items: list[AdminEnvSettingUpdate]


class AdminEnvSettingsUpdateResponse(BaseModel):
    updated_keys: list[str]
    requires_restart: bool = True


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


class AdminRecentPostInfo(BaseModel):
    id: int
    user_id: int
    user_email: str | None = None
    title: str
    status: str
    input_tokens: int
    output_tokens: int
    credit_cost: float
    created_at: datetime


class AdminPostDetailResponse(AdminRecentPostInfo):
    content: str | None = None
    prompt: str | None = None
    ai_provider: str | None = None
    ai_model: str | None = None
    llm_call_count: int = 0
    diagnostics: list[dict] = []
    usage: dict | None = None


class AdminGeminiTestRequest(BaseModel):
    provider: str = "gemini_api_key"
    api_key: str = ""
    service_account_json: str = ""
    model: str = ""


class AdminGeminiTestResponse(BaseModel):
    ok: bool
    message: str
    models: list[str] = []


class AdminDashboardResponse(BaseModel):
    metrics: AdminMetricResponse
    users: list[AdminUserInfo]
    model_pricing: list[ModelPricingResponse]
    recent_payments: list[AdminPaymentInfo] = []
    recent_posts: list[AdminRecentPostInfo] = []
