import { Link } from "react-router-dom";
import { getGoogleLoginUrl } from "@/services/apiService";

function GoogleRegister() {
  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-kicker">Tạo tài khoản</div>
        <h2>Tạo tài khoản bằng Google</h2>
        <p className="auth-subtitle">
          Tài khoản sẽ được tạo tự động sau khi Google xác thực email của bạn, sau đó bạn có thể vào khu làm việc ngay.
        </p>

        <a
          href={getGoogleLoginUrl("/create-post")}
          className="btn btn-generate"
          style={{ display: "inline-block", textDecoration: "none", textAlign: "center" }}
        >
          Đăng ký với Google
        </a>

        <p className="auth-footer">
          Đã có tài khoản? <Link to="/login">Đăng nhập</Link>
        </p>
      </div>
    </div>
  );
}

export default GoogleRegister;
