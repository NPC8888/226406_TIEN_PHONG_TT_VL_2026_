import base64
import hashlib
import hmac
import os
from datetime import datetime
from urllib.parse import quote


SIGNED_FIELD_ORDER = [
    "order_amount",
    "merchant",
    "currency",
    "operation",
    "order_description",
    "order_invoice_number",
    "customer_id",
    "payment_method",
    "success_url",
    "error_url",
    "cancel_url",
]


def get_sepay_config() -> dict:
    environment = os.getenv("SEPAY_ENVIRONMENT", "sandbox").strip().lower()
    is_production = environment == "production"
    return {
        "payment_mode": os.getenv("SEPAY_PAYMENT_MODE", "checkout").strip().lower(),
        "merchant_id": os.getenv("SEPAY_MERCHANT_ID"),
        "secret_key": os.getenv("SEPAY_SECRET_KEY"),
        "ipn_secret_key": os.getenv("SEPAY_IPN_SECRET_KEY"),
        "webhook_secret_key": os.getenv("SEPAY_WEBHOOK_SECRET_KEY") or os.getenv("SEPAY_IPN_SECRET_KEY"),
        "webhook_tolerance_seconds": int(os.getenv("SEPAY_WEBHOOK_TOLERANCE_SECONDS", "900")),
        "environment": environment,
        "checkout_url": os.getenv(
            "SEPAY_CHECKOUT_URL",
            "https://pay.sepay.vn/v1/checkout/init" if is_production else "https://pay-sandbox.sepay.vn/v1/checkout/init",
        ),
        "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/"),
        "vnd_per_credit": int(os.getenv("SEPAY_VND_PER_CREDIT", "25000")),
        "bank_code": os.getenv("SEPAY_BANK_CODE"),
        "account_number": os.getenv("SEPAY_ACCOUNT_NUMBER"),
        "account_holder": os.getenv("SEPAY_ACCOUNT_HOLDER", ""),
        "store_name": os.getenv("SEPAY_STORE_NAME", "Intener"),
    }


def require_sepay_checkout_config() -> dict:
    config = get_sepay_config()
    missing = [key for key in ("merchant_id", "secret_key") if not config[key]]
    if missing:
        raise RuntimeError(f"Missing SePay configuration: {', '.join(missing)}")
    return config


def require_sepay_qr_config() -> dict:
    config = get_sepay_config()
    missing = [key for key in ("bank_code", "account_number") if not config[key]]
    if missing:
        raise RuntimeError(f"Missing SePay QR configuration: {', '.join(missing)}")
    return config


def sign_checkout_fields(fields: dict, secret_key: str) -> str:
    signed_parts = []
    for field in SIGNED_FIELD_ORDER:
        value = fields.get(field)
        if value is None:
            continue
        signed_parts.append(f"{field}={value}")
    signed_string = ",".join(signed_parts)
    digest = hmac.new(secret_key.encode("utf-8"), signed_string.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def build_invoice_number(user_id: int, credits: int) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"INTENER_{user_id}_{credits}_{timestamp}"


def build_checkout_fields(*, user_id: int, credits: int, amount_vnd: int, invoice_number: str) -> dict:
    config = require_sepay_checkout_config()
    fields = {
        "order_amount": str(amount_vnd),
        "merchant": config["merchant_id"],
        "currency": "VND",
        "operation": "PURCHASE",
        "order_description": f"Nap {credits} credit Intener",
        "order_invoice_number": invoice_number,
        "customer_id": f"USER_{user_id}",
        "payment_method": "BANK_TRANSFER",
        "success_url": f"{config['frontend_url']}/plans?payment=success&invoice={invoice_number}",
        "error_url": f"{config['frontend_url']}/plans?payment=error&invoice={invoice_number}",
        "cancel_url": f"{config['frontend_url']}/plans?payment=cancel&invoice={invoice_number}",
    }
    fields["signature"] = sign_checkout_fields(fields, config["secret_key"])
    return fields


def build_qr_url(*, amount_vnd: int, invoice_number: str) -> str:
    config = require_sepay_qr_config()
    params = [
        f"acc={quote(config['account_number'])}",
        f"bank={quote(config['bank_code'])}",
        f"amount={amount_vnd}",
        f"des={quote(invoice_number)}",
        "template=compact",
        "showinfo=true",
    ]
    if config["account_holder"]:
        params.append(f"holder={quote(config['account_holder'])}")
    if config["store_name"]:
        params.append(f"store={quote(config['store_name'])}")
    return "https://qr.sepay.vn/img?" + "&".join(params)
