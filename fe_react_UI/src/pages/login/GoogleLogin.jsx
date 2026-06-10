import { useMemo } from "react";
import { Link, useLocation } from "react-router-dom";
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
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-kicker">Đăng nhập</div>
        <h2>Đăng nhập với Google</h2>
        <p className="auth-subtitle">
          Xác thực nhanh để vào khu làm việc tạo bài, lưu lịch sử và sử dụng các tính năng theo gói của bạn.
        </p>

        {authError && <div className="auth-error">Không thể đăng nhập bằng Google: {authError}</div>}

        <a
          href={googleLoginUrl}
          className="btn btn-generate"
          style={{ display: "inline-block", textDecoration: "none", textAlign: "center" }}
        >
          Tiếp tục với Google
        </a>

        <p className="auth-footer">
          Chưa có tài khoản? <Link to="/register">Tạo tài khoản bằng Google</Link>
        </p>
      </div>
    </div>
  );
}

export default GoogleLogin;
