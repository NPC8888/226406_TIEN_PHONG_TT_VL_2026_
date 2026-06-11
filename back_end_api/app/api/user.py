from datetime import datetime, timedelta
import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from fastapi import APIRouter, Depends, Header, HTTPException, Request as FastAPIRequest, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.payment import Payment
from app.repositories import user_repository
from app.schemas.auth_schemas import (
    UserRegister,
    LoginRequest,
    GoogleLoginRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.plan_schemas import PlanResponse
from app.schemas.subscription_schemas import PaymentCheckoutResponse, SubscriptionPurchaseRequest, SubscriptionResponse
from app.services.credit_service import CREDIT_PACKAGES, apply_paid_credits
from app.services.sepay_service import (
    build_checkout_fields,
    build_invoice_number,
    build_qr_url,
    get_sepay_config,
    require_sepay_checkout_config,
    require_sepay_qr_config,
)
from app.services.auth_service import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_google_oauth_state,
    decode_google_oauth_state,
    decode_access_token,
)
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv

load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
GOOGLE_TOKEN_CLOCK_SKEW_SECONDS = int(os.getenv("GOOGLE_TOKEN_CLOCK_SKEW_SECONDS", "10"))

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_repository.get_user_by_id(db, int(payload["sub"]))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def verify_google_token(token: str) -> dict:
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=GOOGLE_TOKEN_CLOCK_SKEW_SECONDS,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Google token: {exc}")

    if idinfo.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")

    if not idinfo.get("email_verified"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google email is not verified")

    return idinfo


def require_google_oauth_settings() -> None:
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Missing GOOGLE_CLIENT_ID")
    if not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Missing GOOGLE_CLIENT_SECRET")
    if not GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Missing GOOGLE_REDIRECT_URI")
    if not FRONTEND_URL:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Missing FRONTEND_URL")


def build_frontend_redirect(next_path: str, **query_params: str) -> str:
    base_url = FRONTEND_URL.rstrip("/")
    safe_path = next_path if next_path.startswith("/") else f"/{next_path}"
    query_string = urlencode(query_params)
    if query_string:
        return f"{base_url}{safe_path}?{query_string}"
    return f"{base_url}{safe_path}"


def exchange_google_code_for_tokens(code: str) -> dict:
    payload = urlencode(
        {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")
    request = Request(
        "https://oauth2.googleapis.com/token",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange Google authorization code: {exc}",
        )


def get_or_create_google_user(db: Session, google_claims: dict):
    email = google_claims["email"]
    name = google_claims.get("name")
    google_id = google_claims["sub"]
    avatar_url = google_claims.get("picture")

    user = user_repository.get_user_by_google_id(db, google_id)
    if user:
        return user

    existing_user = user_repository.get_user_by_email(db, email)
    if existing_user:
        if existing_user.google_id and existing_user.google_id != google_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google account mismatch")
        if existing_user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered with password login",
            )
        existing_user.google_id = google_id
        if not existing_user.name and name:
            existing_user.name = name
        if avatar_url:
            existing_user.avatar_url = avatar_url
        db.commit()
        db.refresh(existing_user)
        return existing_user

    return user_repository.create_user(
        db,
        email=email,
        name=name,
        google_id=google_id,
        avatar_url=avatar_url,
    )


@router.post("/auth/register", response_model=TokenResponse)
def register_user(user_create: UserRegister, db: Session = Depends(get_db)):
    existing_user = user_repository.get_user_by_email(db, user_create.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = get_password_hash(user_create.password)
    user = user_repository.create_user(
        db,
        email=user_create.email,
        password_hash=hashed_password,
        name=user_create.name,
        avatar_url=None,
    )

    access_token = create_access_token(subject=str(user.id), expires_delta=timedelta(hours=2))
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/login", response_model=TokenResponse)
def login_user(login_request: LoginRequest, db: Session = Depends(get_db)):
    user = user_repository.get_user_by_email(db, login_request.email)
    if user is None or user.password_hash is None or not verify_password(login_request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token(subject=str(user.id), expires_delta=timedelta(hours=2))
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/auth/google-login", response_model=TokenResponse)
def google_login(google_request: GoogleLoginRequest, db: Session = Depends(get_db)):
    idinfo = verify_google_token(google_request.id_token)
    user = get_or_create_google_user(db, idinfo)

    access_token = create_access_token(subject=str(user.id), expires_delta=timedelta(hours=2))
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/auth/google/login")
def start_google_login(next: str = "/"):
    require_google_oauth_settings()
    state = create_google_oauth_state(next_path=next)
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
        {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "prompt": "select_account",
            "state": state,
        }
    )
    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@router.get("/auth/google/callback")
def google_callback(code: str | None = None, state: str | None = None, error: str | None = None, db: Session = Depends(get_db)):
    require_google_oauth_settings()

    if error:
        return RedirectResponse(
            url=build_frontend_redirect("/", auth_error=error),
            status_code=status.HTTP_302_FOUND,
        )

    if not code or not state:
        return RedirectResponse(
            url=build_frontend_redirect("/", auth_error="missing_google_callback_params"),
            status_code=status.HTTP_302_FOUND,
        )

    state_payload = decode_google_oauth_state(state)
    if state_payload is None:
        return RedirectResponse(
            url=build_frontend_redirect("/", auth_error="invalid_google_oauth_state"),
            status_code=status.HTTP_302_FOUND,
        )

    token_data = exchange_google_code_for_tokens(code)
    google_id_token = token_data.get("id_token")
    if not google_id_token:
        return RedirectResponse(
            url=build_frontend_redirect("/", auth_error="missing_google_id_token"),
            status_code=status.HTTP_302_FOUND,
        )

    google_claims = verify_google_token(google_id_token)
    user = get_or_create_google_user(db, google_claims)
    access_token = create_access_token(subject=str(user.id), expires_delta=timedelta(hours=2))

    next_path = state_payload.get("next") or "/"
    return RedirectResponse(
        url=build_frontend_redirect(next_path, token=access_token),
        status_code=status.HTTP_302_FOUND,
    )


@router.get("/auth/me", response_model=UserResponse)
def get_profile(current_user=Depends(get_current_user)):
    return current_user


@router.get("/plans", response_model=list[PlanResponse])
def list_plans():
    vnd_per_credit = get_sepay_config()["vnd_per_credit"]
    return [
        {
            "id": credits,
            "name": f"{credits} Credit",
            "slug": f"credit-{credits}",
            "price_cents": credits * vnd_per_credit,
            "currency": "VND",
            "max_posts_per_day": 0,
            "credit_amount": credits,
            "description": f"Nạp {credits} credit vào tài khoản. Thanh toán qua SePay.",
        }
        for credits in CREDIT_PACKAGES
    ]


@router.get("/credits/packages", response_model=list[PlanResponse])
def list_credit_packages():
    return list_plans()


@router.post("/subscriptions/purchase", response_model=PaymentCheckoutResponse)
def purchase_subscription(
    purchase: SubscriptionPurchaseRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        config = get_sepay_config()
        credits = int(str(purchase.plan_slug).removeprefix("credit-"))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit package not found")

    if credits not in CREDIT_PACKAGES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credit package not found")

    amount_vnd = credits * config["vnd_per_credit"]
    invoice_number = build_invoice_number(current_user.id, credits)
    fields = {}
    qr_url = None
    checkout_url = None
    method = "POST"
    provider = "sepay"
    bank_config = {}

    try:
        if config["payment_mode"] == "webhook_qr":
            bank_config = require_sepay_qr_config()
            qr_url = build_qr_url(amount_vnd=amount_vnd, invoice_number=invoice_number)
            method = "QR"
            provider = "sepay_webhook"
        else:
            config = require_sepay_checkout_config()
            checkout_url = config["checkout_url"]
            fields = build_checkout_fields(
                user_id=current_user.id,
                credits=credits,
                amount_vnd=amount_vnd,
                invoice_number=invoice_number,
            )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    payment = Payment(
        user_id=current_user.id,
        provider=provider,
        provider_payment_id=invoice_number,
        amount_cents=amount_vnd,
        currency="VND",
        status="pending",
        metadata_json={
            "credit_amount": credits,
            "invoice_number": invoice_number,
            "environment": config["environment"],
            "payment_mode": config["payment_mode"],
            "qr_url": qr_url,
            "bank_code": bank_config.get("bank_code"),
            "account_number": bank_config.get("account_number"),
        },
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "checkout_url": checkout_url,
        "method": method,
        "fields": fields,
        "invoice_number": invoice_number,
        "payment_id": payment.id,
        "amount_vnd": amount_vnd,
        "credits": credits,
        "status": payment.status,
        "qr_url": qr_url,
        "bank_code": bank_config.get("bank_code"),
        "account_number": bank_config.get("account_number"),
        "account_holder": bank_config.get("account_holder"),
        "transfer_content": invoice_number,
    }


@router.post("/payments/sepay/ipn")
def sepay_ipn(
    payload: dict,
    x_secret_key: str | None = Header(default=None, alias="X-Secret-Key"),
    db: Session = Depends(get_db),
):
    config = get_sepay_config()
    if config["ipn_secret_key"] and x_secret_key != config["ipn_secret_key"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid SePay IPN secret")

    notification_type = payload.get("notification_type")
    order = payload.get("order") or {}
    transaction = payload.get("transaction") or {}
    invoice_number = order.get("order_invoice_number")
    transaction_status = transaction.get("transaction_status")

    if not invoice_number:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing invoice number")

    payment = db.query(Payment).filter(Payment.provider == "sepay", Payment.provider_payment_id == invoice_number).first()
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    metadata = dict(payment.metadata_json or {})
    metadata["sepay_ipn"] = payload
    metadata["sepay_transaction_id"] = transaction.get("transaction_id") or transaction.get("id")

    if payment.status == "completed":
        payment.metadata_json = metadata
        db.commit()
        return {"success": True}

    if notification_type == "ORDER_PAID" and transaction_status == "APPROVED":
        expected_amount = int(payment.amount_cents or 0)
        paid_amount = int(float(transaction.get("transaction_amount") or order.get("order_amount") or 0))
        if paid_amount < expected_amount:
            payment.metadata_json = {**metadata, "amount_mismatch": {"expected": expected_amount, "paid": paid_amount}}
            db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment amount mismatch")

        credits = int(metadata.get("credit_amount") or 0)
        user = user_repository.get_user_by_id(db, payment.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        payment.status = "completed"
        payment.metadata_json = metadata
        apply_paid_credits(db, user, credits)
        db.refresh(payment)
        return {"success": True}

    if notification_type == "TRANSACTION_VOID":
        payment.status = "failed"
        payment.metadata_json = metadata
        db.commit()
        return {"success": True}

    payment.metadata_json = metadata
    db.commit()
    return {"success": True}


def verify_sepay_webhook_auth(
    *,
    raw_body: bytes,
    x_secret_key: str | None,
    x_sepay_signature: str | None,
    x_sepay_timestamp: str | None,
) -> None:
    config = get_sepay_config()
    secret = config["webhook_secret_key"]
    if not secret:
        return

    if x_sepay_signature and x_sepay_timestamp:
        try:
            timestamp = int(x_sepay_timestamp)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid SePay timestamp")

        if abs(int(time.time()) - timestamp) > int(config["webhook_tolerance_seconds"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="SePay webhook request expired")

        signed_payload = f"{timestamp}.".encode("utf-8") + raw_body
        expected = "sha256=" + hmac.new(
            secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, x_sepay_signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid SePay webhook signature")
        return

    if x_secret_key != secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid SePay webhook secret")


def _normalize_payment_text(value: str) -> str:
    return "".join(ch for ch in str(value or "").upper() if ch.isalnum())


def _flatten_payload_values(value) -> list[str]:
    if isinstance(value, dict):
        values = []
        for item in value.values():
            values.extend(_flatten_payload_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_flatten_payload_values(item))
        return values
    return [str(value)] if value is not None else []


def _find_pending_sepay_payment(db: Session, payload: dict) -> Payment | None:
    content_fields = [
        payload.get("content"),
        payload.get("description"),
        payload.get("transactionContent"),
        payload.get("transaction_content"),
        payload.get("paymentCode"),
        payload.get("payment_code"),
        payload.get("code"),
        payload.get("referenceCode"),
        payload.get("reference_code"),
        payload.get("id"),
    ]
    haystack = " ".join(str(item or "") for item in content_fields + _flatten_payload_values(payload))
    normalized_haystack = _normalize_payment_text(haystack)

    candidates = (
        db.query(Payment)
        .filter(Payment.provider == "sepay_webhook")
        .filter(Payment.status == "pending")
        .order_by(Payment.created_at.asc())
        .limit(100)
        .all()
    )
    for candidate in candidates:
        invoice = candidate.provider_payment_id or ""
        if invoice and (invoice in haystack or _normalize_payment_text(invoice) in normalized_haystack):
            return candidate
    return None


@router.post("/payments/sepay/webhook")
async def sepay_bank_webhook(
    request: FastAPIRequest,
    x_secret_key: str | None = Header(default=None, alias="X-Secret-Key"),
    x_sepay_signature: str | None = Header(default=None, alias="X-SePay-Signature"),
    x_sepay_timestamp: str | None = Header(default=None, alias="X-SePay-Timestamp"),
    db: Session = Depends(get_db),
):
    raw_body = await request.body()
    verify_sepay_webhook_auth(
        raw_body=raw_body,
        x_secret_key=x_secret_key,
        x_sepay_signature=x_sepay_signature,
        x_sepay_timestamp=x_sepay_timestamp,
    )

    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid SePay webhook JSON")

    transfer_type = str(payload.get("transferType") or payload.get("transfer_type") or "").lower()
    if transfer_type and transfer_type != "in":
        return {"success": True}

    amount = int(float(payload.get("transferAmount") or payload.get("transfer_amount") or payload.get("amount") or 0))
    payment = _find_pending_sepay_payment(db, payload)

    if payment is None:
        print(f"[SePayWebhook] unmatched payload={payload}")
        return {"success": True, "matched": False}

    metadata = dict(payment.metadata_json or {})
    metadata["sepay_webhook"] = payload
    metadata["sepay_reference_code"] = payload.get("referenceCode") or payload.get("reference_code") or payload.get("id")

    if payment.status == "completed":
        payment.metadata_json = metadata
        db.commit()
        return {"success": True, "matched": True}

    expected_amount = int(payment.amount_cents or 0)
    if amount < expected_amount:
        payment.metadata_json = {**metadata, "amount_mismatch": {"expected": expected_amount, "paid": amount}}
        db.commit()
        return {"success": True, "matched": True, "paid": False}

    credits = int(metadata.get("credit_amount") or 0)
    user = user_repository.get_user_by_id(db, payment.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    payment.status = "completed"
    payment.metadata_json = metadata
    apply_paid_credits(db, user, credits)
    db.refresh(payment)
    return {"success": True, "matched": True, "paid": True}


@router.get("/subscriptions/active", response_model=SubscriptionResponse | None)
def active_subscription(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "user_id": current_user.id,
        "credit_balance": float(current_user.credit_balance or 0),
        "purchased_credits": 0,
        "total_input_tokens": current_user.total_input_tokens or 0,
        "total_output_tokens": current_user.total_output_tokens or 0,
        "total_credit_spent": float(current_user.total_credit_spent or 0),
    }


@router.get("/credits/balance", response_model=SubscriptionResponse)
def credit_balance(current_user=Depends(get_current_user)):
    return {
        "user_id": current_user.id,
        "credit_balance": float(current_user.credit_balance or 0),
        "purchased_credits": 0,
        "total_input_tokens": current_user.total_input_tokens or 0,
        "total_output_tokens": current_user.total_output_tokens or 0,
        "total_credit_spent": float(current_user.total_credit_spent or 0),
    }
    
