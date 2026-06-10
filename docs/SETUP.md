# Huong Dan Setup Du An Intener

Tai lieu nay dung cho truong hop vua clone project ve may moi. Mac dinh luc do chua co:

- `back_end_api/venv`
- `fe_react_UI/node_modules`
- `back_end_api/.env`
- `fe_react_UI/.env`
- database MySQL

Du an co script setup tu dong de cai nhanh phan lon moi thu. Sau khi chay script, ban van can sua `.env`, tao database, chay migration va start server.

## 1. Yeu Cau Truoc Khi Cai

Can cai san tren may:

- Python 3.10 tro len
- Node.js 20 tro len
- npm
- MySQL 8 tro len
- Git neu clone tu repository
- PowerShell neu dung Windows

Kiem tra nhanh:

```powershell
python --version
node --version
npm --version
```

Neu may chua co MySQL, cai MySQL Server truoc roi ghi lai:

- host, thuong la `localhost`
- port, thuong la `3306`
- username, vi du `root`
- password
- ten database muon dung

## 2. Clone Project

```powershell
git clone <repo-url>
cd project_intener
```

Neu da co source san tren may, mo terminal tai thu muc goc:

```powershell
cd D:\project_intener
```

Thu muc goc phai co cac file/folder nhu sau:

```text
back_end_api/
fe_react_UI/
docs/
setup.ps1
setup.sh
README.md
```

## 3. Cai Dat Nhanh Bang Script

### Windows PowerShell

Chay tai thu muc goc project:

```powershell
.\setup.ps1
```

Neu PowerShell bao chan script, chay lenh nay mot lan:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Sau do chay lai:

```powershell
.\setup.ps1
```

### Git Bash, WSL, Linux hoac macOS

```bash
chmod +x setup.sh
./setup.sh
```

### Script se lam gi?

Script se tu dong:

- Tao `back_end_api/venv` neu chua co.
- Cai dependency backend tu `back_end_api/requirements.txt`.
- Tao `back_end_api/.env` tu `back_end_api/.env.example` neu chua co.
- Cai dependency frontend trong `fe_react_UI`.
- Tao `fe_react_UI/.env` neu chua co.
- Kiem tra compile backend.
- Build frontend de bat loi som.

Script khong tu tao database MySQL va khong tu dien API key cho ban.

## 4. Cau Hinh Backend `.env`

Mo file:

```text
back_end_api/.env
```

Neu file chua ton tai, tao tu file mau:

```powershell
cd back_end_api
Copy-Item .env.example .env
```

Cac bien quan trong can sua:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=intener

JWT_SECRET_KEY=change_this_to_a_long_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

FRONTEND_URL=http://localhost:5173

ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_this_admin_password
ADMIN_EMAIL=admin@your-domain.com

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash

GROQ_API_KEY=your_groq_api_key
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.3-70b-versatile

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

SEPAY_ENVIRONMENT=sandbox
SEPAY_PAYMENT_MODE=webhook_qr
SEPAY_WEBHOOK_SECRET_KEY=your_sepay_webhook_secret_key
SEPAY_WEBHOOK_TOLERANCE_SECONDS=900
SEPAY_VND_PER_CREDIT=25000
SEPAY_BANK_CODE=VCB
SEPAY_ACCOUNT_NUMBER=your_bank_account_number
SEPAY_ACCOUNT_HOLDER=NGUYEN VAN A
SEPAY_STORE_NAME=Intener
```

Ghi chu:

- `JWT_SECRET_KEY`: tu dat, nen dai va kho doan.
- `ADMIN_PASSWORD`: mat khau dang nhap trang admin.
- `MYSQL_DATABASE`: phai trung voi database se tao o buoc tiep theo.
- Neu chi test tinh nang co ban, co the de trong Google OAuth, Groq hoac SePay. Nhung tinh nang lien quan se khong hoat dong neu thieu key.
- Khong commit `back_end_api/.env` len Git.

Du an cung ho tro `DATABASE_URL` neu muon cau hinh mot dong:

```env
DATABASE_URL=mysql+pymysql://root:your_mysql_password@localhost:3306/intener
```

Neu co `DATABASE_URL`, backend se uu tien bien nay thay cho bo `MYSQL_*`.

## 5. Tao Database MySQL

Dang nhap MySQL bang MySQL Workbench, phpMyAdmin hoac terminal.

Vi du voi MySQL CLI:

```powershell
mysql -u root -p
```

Tao database:

```sql
CREATE DATABASE intener CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Neu muon tao user rieng cho project:

```sql
CREATE USER 'intener_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON intener.* TO 'intener_user'@'localhost';
FLUSH PRIVILEGES;
```

Neu dung user rieng, sua `.env`:

```env
MYSQL_USER=intener_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=intener
```

## 6. Chay Migration Database

Vao backend:

```powershell
cd D:\project_intener\back_end_api
```

Chay migration:

```powershell
.\venv\Scripts\alembic.exe upgrade head
```

Neu dung WSL/Linux/macOS:

```bash
./venv/bin/alembic upgrade head
```

Sau khi thanh cong, database se co cac bang cho user, bai viet, credit, payment, model pricing va cac bang lien quan.

Neu gap loi `Multiple head revisions`, chay:

```powershell
.\venv\Scripts\alembic.exe heads
```

Sau do bao lai danh sach heads hoac tao merge migration. Khong nen xoa file migration tuy tien.

## 7. Chay Backend

Trong thu muc `back_end_api`:

```powershell
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend chay tai:

```text
http://127.0.0.1:8000
```

Swagger API:

```text
http://127.0.0.1:8000/docs
```

## 8. Chay Frontend

Mo terminal moi:

```powershell
cd D:\project_intener\fe_react_UI
npm run dev -- --host 127.0.0.1
```

Frontend chay tai:

```text
http://127.0.0.1:5173
```

Neu frontend can goi backend local, file `fe_react_UI/.env` nen co:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 9. Dang Nhap Admin

Mo:

```text
http://127.0.0.1:5173/admin
```

Tai khoan admin lay trong `back_end_api/.env`:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_this_admin_password
```

## 10. Test Thanh Toan SePay Local

SePay khong goi duoc `localhost`, nen khi test webhook local can public URL bang tunnel.

Co the dung Cloudflare Tunnel:

```powershell
cloudflared tunnel --url http://localhost:8000
```

Hoac ngrok:

```powershell
ngrok http 8000
```

Lay URL public, vi du:

```text
https://abc.trycloudflare.com
```

Trong SePay, cau hinh webhook:

```text
https://abc.trycloudflare.com/payments/sepay/webhook
```

Phan bao mat webhook nen chon:

```text
HMAC-SHA256
```

Secret tren SePay phai trung voi:

```env
SEPAY_WEBHOOK_SECRET_KEY=your_sepay_webhook_secret_key
```

Sau khi sua `.env`, restart backend.

## 11. Kiem Tra Sau Khi Cai

Backend compile:

```powershell
cd D:\project_intener\back_end_api
.\venv\Scripts\python.exe -m compileall app alembic
```

Frontend build:

```powershell
cd D:\project_intener\fe_react_UI
npm run build
```

Frontend lint:

```powershell
npm run lint
```

Luu y: neu lint bao loi cu, can xu ly rieng. Lint khong phai buoc bat buoc de chay local.

## 12. Cac Thu Muc Va File Khong Nen Commit

Khong commit:

```text
back_end_api/venv/
fe_react_UI/node_modules/
fe_react_UI/dist/
**/__pycache__/
back_end_api/.env
back_end_api/service-account.json
```

Nen dam bao `.gitignore` da co cac dong tren.

## 13. Lenh Chay Nhanh Hang Ngay

Sau khi da setup xong, moi lan mo project chi can chay backend va frontend.

Terminal 1:

```powershell
cd D:\project_intener\back_end_api
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
cd D:\project_intener\fe_react_UI
npm run dev -- --host 127.0.0.1
```

