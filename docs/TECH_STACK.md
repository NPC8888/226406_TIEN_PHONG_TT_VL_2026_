# Cong Nghe Su Dung Trong Du An

Tai lieu nay tom tat cac cong nghe, thu vien va dich vu chinh dang duoc dung trong project Intener.

## Tong Quan Kien Truc

Project gom 2 phan chinh:

- Backend API: FastAPI
- Frontend UI: React + Vite

He thong luu du lieu trong MySQL, dung Alembic de migration schema, dung JWT cho auth, dung Google/Vertex Gemini va Groq cho AI, dung SePay WebHook de nap credit bang chuyen khoan.

## Backend

### Python

Backend viet bang Python.

Vai tro:

- Xu ly API.
- Ket noi database.
- Goi AI provider.
- Tinh credit.
- Xu ly thanh toan SePay.
- Quan ly auth va admin dashboard.

### FastAPI

Framework API chinh.

Vai tro:

- Tao REST API.
- Khai bao router.
- Validate request/response bang Pydantic.
- Tao Swagger docs tai `/docs`.

File chinh:

```text
back_end_api/app/main.py
back_end_api/app/api/
```

### SQLAlchemy

ORM de lam viec voi database.

Vai tro:

- Dinh nghia model.
- Query user, post, payment, pricing.
- Quan ly session database.

File chinh:

```text
back_end_api/app/db.py
back_end_api/app/models/
back_end_api/app/repositories/
```

### Alembic

Cong cu migration database.

Vai tro:

- Tao/sua schema database theo tung revision.
- Chay migration bang `alembic upgrade head`.

Thu muc:

```text
back_end_api/alembic/
back_end_api/alembic/versions/
```

### MySQL

Database chinh cua project.

Luu:

- Users
- Posts
- Post history
- Payments
- Model pricing
- Subscriptions/credit data

### Pydantic

Dung trong FastAPI de validate schema request/response.

Thu muc:

```text
back_end_api/app/schemas/
```

### JWT

Dung cho dang nhap email/password, Google login callback va admin access token.

Thu vien:

```text
python-jose
```

File chinh:

```text
back_end_api/app/services/auth_service.py
```

### Passlib + Bcrypt

Dung de hash password user.

Thu vien:

```text
passlib[bcrypt]
```

## AI Providers

### Vertex Gemini

Dung de sinh noi dung bai viet.

Model dang ho tro:

```text
gemini-2.5-flash-lite
gemini-3-flash-preview
```

File chinh:

```text
back_end_api/app/services/vertex_gemini_service.py
```

Yeu cau:

- Google Cloud project
- Vertex AI API
- Service account JSON
- Quyen goi Vertex AI

### Groq

Dung cho mot so tac vu goi AI/gợi ý trong service hien co.

File chinh:

```text
back_end_api/app/services/groq_service.py
```

Bien moi truong:

```env
GROQ_API_KEY=
GROQ_BASE_URL=
GROQ_MODEL=
```

## Credit System

Credit duoc tinh theo token input/output.

File chinh:

```text
back_end_api/app/services/credit_service.py
```

Bang lien quan:

```text
users.credit_balance
users.total_input_tokens
users.total_output_tokens
users.total_credit_spent
model_pricing
payments
```

Admin co the xem va cap nhat gia model trong dashboard.

## Thanh Toan

### SePay WebHook QR

Project dang ho tro che do:

```env
SEPAY_PAYMENT_MODE=webhook_qr
```

Luồng:

1. User chon goi credit.
2. Backend tao payment pending.
3. Frontend hien QR chuyen khoan.
4. User chuyen khoan dung so tien va noi dung.
5. SePay gui webhook ve backend.
6. Backend verify HMAC-SHA256.
7. Backend match invoice va cong credit.

Endpoint:

```text
POST /payments/sepay/webhook
```

File chinh:

```text
back_end_api/app/services/sepay_service.py
back_end_api/app/api/user.py
```

### HMAC-SHA256

Dung de xac thuc webhook SePay.

Header SePay gui:

```text
X-SePay-Signature
X-SePay-Timestamp
```

Backend verify bang secret:

```env
SEPAY_WEBHOOK_SECRET_KEY=
```

## Frontend

### React

Thu vien UI chinh.

Thu muc:

```text
fe_react_UI/src/
```

### Vite

Dev server va build tool.

Lenh:

```powershell
npm run dev
npm run build
```

### React Router

Dung de quan ly route frontend.

File chinh:

```text
fe_react_UI/src/routes/AppRouter.jsx
```

Route tieu bieu:

```text
/
/login
/register
/plans
/create-post
/history
/admin
```

### Context API

Dung de luu auth state, user profile va subscription/credit state.

File chinh:

```text
fe_react_UI/src/contexts/AuthContext.jsx
```

### CSS Modules

Dung cho mot so component/page co style rieng.

Vi du:

```text
src/pages/admin/Admin.module.css
src/components/PostForm/PostFormModern.module.css
```

## Export PDF

Thu vien:

```text
jspdf
html2canvas
jszip
```

Vai tro:

- Render HTML bai viet thanh canvas.
- Chia canvas thanh cac trang A4.
- Tao file PDF.
- Gom nhieu PDF vao ZIP khi export batch.

File chinh:

```text
fe_react_UI/src/utils/htmlToPdf.js
fe_react_UI/src/utils/pdfExport.js
fe_react_UI/src/utils/downloadHtmlAsPdf.js
```

## Cac Thu Vien Frontend Khac

### Bootstrap

Dung cho mot so style/component co san.

### DOMPurify

Co trong dependency tree, huu ich khi can sanitize HTML.

### html2canvas

Dung de chup DOM thanh canvas khi export PDF.

### jsPDF

Dung de tao file PDF tren trinh duyet.

### JSZip

Dung de gom nhieu PDF thanh file ZIP.

## Cong Cu Kiem Tra

### ESLint

Dung de lint frontend:

```powershell
npm run lint
```

### compileall

Dung de kiem tra syntax Python:

```powershell
python -m compileall app alembic
```

## Tom Tat Dependency Chinh

Backend:

```text
fastapi
uvicorn
sqlalchemy
pymysql
alembic
python-dotenv
python-jose
passlib
google-auth
openai
requests
email-validator
```

Frontend:

```text
react
react-dom
react-router-dom
vite
bootstrap
html2canvas
jspdf
jszip
eslint
```
