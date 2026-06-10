# Gioi Thieu Du An Intener

## 1. Tong Quan

Intener la ung dung web ho tro tao noi dung bai viet bang tri tue nhan tao. Nguoi dung co the nhap danh sach tieu de, phong cach viet, cau truc bai viet va so tu mong muon cho tung phan. He thong se goi AI de tao noi dung hoan chinh, luu lai lich su va cho phep xuat ket qua ra PDF.

Du an duoc xay dung theo mo hinh full-stack:

- Frontend React de nguoi dung thao tac truc quan.
- Backend FastAPI de xu ly API, auth, database, AI va thanh toan.
- MySQL de luu thong tin nguoi dung, lich su bai viet, giao dich va credit.
- SePay WebHook de nap credit qua chuyen khoan ngan hang.
- Vertex Gemini/Groq de sinh noi dung va goi y.

## 2. Bai Toan Du An Giai Quyet

Viec tao noi dung thuong ton nhieu thoi gian o cac buoc:

- Nghien cuu cau truc bai viet.
- Chia dàn ý thanh cac muc hop ly.
- Viet noi dung theo phong cach mong muon.
- Tao nhieu bai tu nhieu tieu de khac nhau.
- Luu va quan ly cac ban noi dung da tao.
- Xuat noi dung thanh file de gui, in hoac luu tru.

Intener giai quyet cac van de nay bang cach bien quy trinh tao bai viet thanh mot workflow co cau truc:

1. Nhap tieu de.
2. Chon phong cach viet.
3. Tao/chinh sua dàn ý.
4. Chon model AI.
5. Uoc tinh credit.
6. Tao bai viet.
7. Luu lich su.
8. Xuat PDF.

## 3. Doi Tuong Su Dung

Du an phu hop voi:

- Nguoi viet content.
- Chu shop/cua hang can tao bai quang cao.
- Nguoi lam marketing.
- Sinh vien can tao nhap ban noi dung co cau truc.
- Nhom van hanh website/blog.
- Admin quan ly he thong AI credit.

## 4. Tinh Nang Cho Nguoi Dung

### Dang Ky Va Dang Nhap

Nguoi dung co the:

- Dang ky bang email/password.
- Dang nhap bang email/password.
- Dang nhap bang Google OAuth neu da cau hinh Google credentials.

### Tao Bai Viet Bang AI

Nguoi dung co the:

- Nhap nhieu tieu de cung luc.
- Nhap phong cach viet.
- Tao nhieu muc trong dàn ý.
- Cau hinh vai tro, mo ta va so tu cho tung muc.
- Goi y phong cach viet bang AI.
- Goi y cau truc bai viet bang AI.
- Chon model sinh bai:
  - Gemini 2.5 Flash-Lite
  - Gemini 3.0 Flash

### Uoc Tinh Va Tru Credit

Truoc khi tao bai, he thong uoc tinh:

- Token input.
- Token output.
- Tong token.
- Chi phi credit du kien.
- So du credit hien co.

Sau khi tao bai, he thong tru credit dua tren token thuc te neu provider tra usage.

### Lich Su Bai Viet

Nguoi dung co the xem lai cac bai da tao trong trang history.

Du lieu luu gom:

- Tieu de.
- Noi dung.
- Dàn ý.
- Token da dung.
- Credit da tieu.
- Thoi gian tao/cap nhat.

### Xuat PDF

Nguoi dung co the:

- Xuat mot bai thanh PDF.
- Xuat nhieu bai thanh ZIP gom nhieu PDF.

PDF duoc render tu HTML noi dung bai viet va chia trang A4.

### Nap Credit

Nguoi dung co the nap credit qua SePay:

1. Chon goi credit.
2. He thong tao QR chuyen khoan.
3. Nguoi dung chuyen khoan dung noi dung.
4. SePay gui WebHook ve backend.
5. Backend xac thuc HMAC-SHA256.
6. He thong cong credit tu dong.

## 5. Tinh Nang Admin

Admin co dashboard rieng tai:

```text
/admin
```

Admin co the xem:

- Tong user.
- Tong bai viet.
- Tong token input/output.
- Tong credit da tieu.
- Doanh thu SePay.
- Cac payment gan day.
- Danh sach user.
- Top user theo credit da tieu.
- Cau hinh gia model AI.

Admin co the cap nhat:

- Ten hien thi model.
- Gia input token theo 1M token.
- Gia output token theo 1M token.
- Trang thai active cua model.

## 6. Luong Hoat Dong Chinh

### Luong Tao Bai Viet

```text
User -> Frontend /create-post
     -> Nhap title/style/sections
     -> Backend estimate credit
     -> User bam tao bai
     -> Backend goi Vertex Gemini
     -> Backend tinh usage va tru credit
     -> Backend luu post/history
     -> Frontend hien ket qua
```

### Luong Nap Credit

```text
User -> Frontend /plans
     -> Chon goi credit
     -> Backend tao payment pending
     -> Frontend hien QR SePay
     -> User chuyen khoan
     -> SePay gui webhook
     -> Backend verify HMAC
     -> Backend match invoice
     -> Backend cong credit
```

### Luong Admin

```text
Admin -> /admin
      -> Dang nhap
      -> Xem dashboard
      -> Theo doi payment/user/token
      -> Cap nhat model pricing
```

## 7. Diem Noi Bat

- Tach ro backend va frontend.
- Co migration database bang Alembic.
- Co co che credit theo token.
- Co admin dashboard.
- Co tich hop SePay WebHook HMAC-SHA256.
- Co ho tro nhieu model Gemini.
- Co xuat PDF/ZIP.
- Co goi y phong cach va cau truc bai viet bang AI.

## 8. Gioi Han Hien Tai

Du an van can hoan thien them truoc khi production:

- Can them test tu dong cho backend/frontend.
- Can don lint frontend.
- Can them `.gitignore` chuan neu repo chua co.
- Can dam bao khong commit `.env`, `service-account.json`, `venv`, `node_modules`.
- Can logging/monitoring tot hon cho production.
- Can co retry va tracking tot hon cho AI provider.
- Can co trang doi soat thanh toan chi tiet hon cho admin.

## 9. Huong Phat Trien

Co the phat trien them:

- Streaming response khi AI dang tao bai.
- Editor chinh sua bai viet sau khi gen.
- Template bai viet theo linh vuc.
- Quan ly workspace/team.
- Goi subscription theo thang.
- Xuat DOCX.
- Thong ke doanh thu theo ngay/thang.
- Retry webhook payment tu admin.
- Email thong bao khi nap credit thanh cong.
- Phan quyen admin chi tiet hon.

## 10. Ket Luan

Intener la mot ung dung AI content generation co day du cac thanh phan nen tang cua mot SaaS nho:

- User auth.
- AI generation.
- Credit billing.
- Payment webhook.
- Admin dashboard.
- History.
- PDF export.

Du an phu hop de tiep tuc hoan thien thanh mot san pham thuc te neu bo sung them test, logging, bao mat production va quy trinh deploy.
