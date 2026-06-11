import { useMemo } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { getGoogleLoginUrl } from "@/services/apiService";

function GoogleLogin() {
  const location = useLocation();
  const { authError } = useAuth();

  const googleLoginUrl = useMemo(() => {
    const nextPath = location.state?.from?.pathname || "/create-post";
    return getGoogleLoginUrl(nextPath);
  }, [location.state]);

  return (
    <div className="auth-page google-auth-page">
      <section className="auth-card google-auth-card" aria-labelledby="google-login-title">
        <div className="google-auth-copy">
          <div className="auth-kicker">Truy cập Smomer</div>
          <h2 id="google-login-title">Đăng nhập an toàn bằng Google</h2>
          <p className="auth-subtitle">
            Dùng tài khoản Google để vào khu làm việc, tạo bài viết, quản lý credit và xem lại lịch sử nội dung của bạn.
          </p>
        </div>

        {authError && <div className="auth-error">Không thể đăng nhập bằng Google: {authError}</div>}

        <a href={googleLoginUrl} className="google-auth-button">
          <span className="google-auth-icon" aria-hidden="true">G</span>
          <span>Tiếp tục với Google</span>
        </a>

        <ul className="google-auth-notes" aria-label="Thông tin đăng nhập">
          <li>Tài khoản mới sẽ được tạo tự động sau khi Google xác thực email.</li>
          <li>Smomer không lưu mật khẩu Google của bạn.</li>
        </ul>
      </section>
    </div>
  );
}

export default GoogleLogin;
