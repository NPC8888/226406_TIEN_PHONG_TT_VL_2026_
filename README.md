# Intener

Intener là ứng dụng web tạo nội dung bằng AI theo hệ thống credit. Người dùng đăng ký hoặc đăng nhập Google, nạp credit, tạo bài viết theo cấu trúc mong muốn, xem lịch sử bài viết và xuất nội dung. Admin có dashboard để theo dõi người dùng, token, doanh thu, thanh toán và cấu hình giá model.

## Tai Lieu Du An

- [Gioi thieu du an](docs/PROJECT_OVERVIEW.md)
- [Cong nghe su dung](docs/TECH_STACK.md)
- [Huong dan cai dat tu dau den cuoi](docs/SETUP.md)

## Tính năng chính

- Đăng ký, đăng nhập bằng email/password hoặc Google OAuth.
- Tạo nội dung bằng AI với cơ chế trừ credit theo token input/output.
- Gợi ý phong cách viết và dàn ý bài viết.
- Lưu lịch sử bài viết đã tạo.
- Trang nạp credit qua SePay.
- IPN SePay để xác nhận thanh toán và cộng credit tự động.
- Dashboard admin theo dõi user, payment, doanh thu, token và cấu hình model pricing.

## Công nghệ sử dụng

- Backend: FastAPI, SQLAlchemy, Alembic, MySQL.
- Frontend: React, Vite, React Router.
- Auth: JWT, Google OAuth.
- AI providers: Vertex Gemini/Groq theo cấu hình service hiện có.
- Payment: SePay Checkout + IPN.

## Cấu trúc thư mục

```text
project_intener/
├── back_end_api/
│   ├── app/
│   │   ├── api/            # FastAPI routers
│   │   ├── models/         # SQLAlchemy models
│   │   ├── repositories/   # Data access layer
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Auth, AI, credit, SePay services
│   ├── alembic/            # Database migrations
│   ├── requirements.txt
│   └── .env.example
└── fe_react_UI/
    ├── src/
    │   ├── components/
    │   ├── contexts/
    │   ├── pages/
    │   ├── routes/
    │   └── services/
    └── package.json
```

## Yêu cầu môi trường

- Python 3.10+
- Node.js 20+
- MySQL 8+
- Tài khoản SePay nếu muốn dùng thanh toán thật hoặc sandbox.
- Google OAuth credentials nếu muốn bật đăng nhập Google.

## Cài đặt backend

Vào thư mục backend:

```powershell
cd back_end_api
```

Tạo virtual environment nếu chưa có:

```powershell
python -m venv venv
```

Kích hoạt môi trường:

```powershell
.\venv\Scripts\Activate.ps1
```

Cài dependency:

```powershell
pip install -r requirements.txt
```

Tạo file `.env` từ mẫu:

```powershell
Copy-Item .env.example .env
```

Cấu hình các biến quan trọng trong `.env`:

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/database_name

JWT_SECRET_KEY=change_this_to_a_strong_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

FRONTEND_URL=http://localhost:5173

ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_this_admin_password
ADMIN_EMAIL=admin@your-domain.com

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

SEPAY_ENVIRONMENT=sandbox
SEPAY_PAYMENT_MODE=webhook_qr
SEPAY_MERCHANT_ID=your_sepay_merchant_id
SEPAY_SECRET_KEY=your_sepay_secret_key
SEPAY_IPN_SECRET_KEY=your_sepay_ipn_secret_key
SEPAY_WEBHOOK_SECRET_KEY=your_sepay_webhook_secret_key
SEPAY_VND_PER_CREDIT=25000
SEPAY_CHECKOUT_URL=https://pay-sandbox.sepay.vn/v1/checkout/init
SEPAY_BANK_CODE=VCB
SEPAY_ACCOUNT_NUMBER=your_bank_account_number
SEPAY_ACCOUNT_HOLDER=NGUYEN VAN A
SEPAY_STORE_NAME=Intener
```

Chạy migration database:

```powershell
alembic upgrade head
```

Chạy backend:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend sẽ chạy tại:

```text
http://127.0.0.1:8000
```

Swagger API docs:

```text
http://127.0.0.1:8000/docs
```

## Cài đặt frontend

Vào thư mục frontend:

```powershell
cd fe_react_UI
```

Cài dependency:

```powershell
npm install
```

Tạo file `.env` nếu cần đổi API URL:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Chạy frontend:

```powershell
npm run dev -- --host 127.0.0.1
```

Frontend sẽ chạy tại:

```text
http://127.0.0.1:5173
```

## Cấu hình SePay

Project hỗ trợ hai chế độ SePay:

- `SEPAY_PAYMENT_MODE=webhook_qr`: phù hợp với tài khoản có mục `Tích hợp WebHooks` và `API Access`. App tạo QR chuyển khoản động, SePay gửi webhook biến động số dư về backend, backend đối chiếu nội dung chuyển khoản và cộng credit.
- `SEPAY_PAYMENT_MODE=checkout`: dùng Cổng thanh toán SePay với `MERCHANT_ID` và `SECRET_KEY`. Chỉ dùng khi tài khoản SePay đã được cấp Payment Gateway merchant.

Với tài khoản SePay thông thường như màn hình có `Tích hợp WebHooks`, dùng:

```env
SEPAY_PAYMENT_MODE=webhook_qr
SEPAY_WEBHOOK_SECRET_KEY=your_webhook_secret
SEPAY_BANK_CODE=VCB
SEPAY_ACCOUNT_NUMBER=your_bank_account_number
SEPAY_ACCOUNT_HOLDER=NGUYEN VAN A
SEPAY_STORE_NAME=Intener
```

Webhook URL cần cấu hình trong SePay:

```text
https://your-domain.com/payments/sepay/webhook
```

Các giá trị lấy ở SePay:

- `SEPAY_WEBHOOK_SECRET_KEY`: vào `Tích hợp WebHooks`, tạo/cập nhật webhook, chọn kiểu xác thực secret key hoặc API key tùy giao diện SePay.
- `SEPAY_BANK_CODE` và `SEPAY_ACCOUNT_NUMBER`: lấy từ tài khoản ngân hàng đã liên kết trong SePay. Bank code dùng short name theo `qr.sepay.vn`, ví dụ `VCB`, `MBBank`, `ACB`, `Techcombank`.
- `SEPAY_ACCOUNT_HOLDER`: tên chủ tài khoản, nên viết không dấu.

Luồng thanh toán hiện tại:

1. Người dùng chọn gói credit ở `/plans`.
2. Frontend gọi backend `/subscriptions/purchase`.
3. Backend tạo payment `pending`, ký form checkout SePay và trả về checkout fields.
4. Frontend submit form POST sang SePay.
5. Sau khi thanh toán, SePay gửi IPN về backend.
6. Backend kiểm tra `X-Secret-Key`, đối chiếu invoice, kiểm tra số tiền và cộng credit.

IPN URL cần cấu hình trên SePay:

```text
https://your-domain.com/payments/sepay/ipn
```

Khi chạy local, SePay không gọi được `localhost`. Dùng một public tunnel như ngrok hoặc localtunnel rồi cấu hình IPN URL theo domain public đó.

Ví dụ với ngrok:

```powershell
ngrok http 8000
```

Sau đó lấy HTTPS URL ngrok và cấu hình:

```text
https://your-ngrok-domain.ngrok-free.app/payments/sepay/ipn
```

## Tài khoản admin

Admin đăng nhập tại:

```text
http://127.0.0.1:5173/admin
```

Thông tin đăng nhập lấy từ `.env` backend:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_this_admin_password
```

Không nên dùng mật khẩu mặc định khi deploy production.

## Lệnh kiểm tra

Backend compile check:

```powershell
cd back_end_api
.\venv\Scripts\python.exe -m compileall app alembic
```

Frontend build:

```powershell
cd fe_react_UI
npm run build
```

Frontend lint:

```powershell
npm run lint
```

Lưu ý: hiện project còn một số lỗi lint cũ trong frontend cần xử lý trước khi coi là production-ready.

## Ghi chú production

Trước khi deploy thật cần xử lý các việc sau:

- Không commit `.env`, `service-account.json`, `venv`, `node_modules`, `dist`, `__pycache__`.
- Thêm `.gitignore` ở root.
- Rotate các secret/key nếu đã từng nằm trong repo.
- Dùng HTTPS cho frontend/backend.
- Cấu hình `JWT_SECRET_KEY`, `ADMIN_PASSWORD`, `SEPAY_SECRET_KEY` đủ mạnh.
- Chạy migration database trước khi release.
- Cấu hình IPN SePay bằng domain public HTTPS.
- Bổ sung test cho auth, credit, payment IPN và generate content.
