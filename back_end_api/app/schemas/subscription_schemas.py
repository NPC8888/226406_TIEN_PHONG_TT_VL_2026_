from pydantic import BaseModel


class SubscriptionPurchaseRequest(BaseModel):
    plan_slug: str


class PaymentCheckoutResponse(BaseModel):
    checkout_url: str | None = None
    method: str = "POST"
    fields: dict[str, str] = {}
    invoice_number: str
    payment_id: int
    amount_vnd: int
    credits: int
    status: str
    qr_url: str | None = None
    bank_code: str | None = None
    account_number: str | None = None
    account_holder: str | None = None
    transfer_content: str | None = None


class SubscriptionResponse(BaseModel):
    user_id: int
    credit_balance: float
    purchased_credits: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_credit_spent: float = 0

    class Config:
        from_attributes = True
