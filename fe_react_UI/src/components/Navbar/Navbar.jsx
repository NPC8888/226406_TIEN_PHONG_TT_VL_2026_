import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import styles from "./Navbar.module.css";

const Navbar = () => {
  const { user, logout, activeSubscription } = useAuth();
  const creditBalance = Number(activeSubscription?.credit_balance ?? user?.credit_balance ?? 0);

  return (
    <nav className={styles.navbar}>
      <div className={styles.navInner}>
        <Link to="/" className={styles.brandArea}>
          <div className={styles.brandCopy}>
            <div className={styles.brandLogo}>Smomer</div>
            <div className={styles.brandTag}>XƯỞNG NỘI DUNG AI</div>
          </div>
        </Link>

        <div className={styles.navLinks}>
          <Link to="/" className={styles.navLink}>
            Giới thiệu
          </Link>
          {user && (
            <Link to="/history" className={styles.navLink}>
              Lịch sử
            </Link>
          )}
          <Link to="/create-post" className={styles.navLink}>
            Tạo bài
          </Link>
        </div>

        <div className={styles.actionsArea}>
          <Link to="/plans" className={styles.creditPill}>
            <span>{creditBalance.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>
            <em>CREDIT</em>
          </Link>
          
          {user ? (
            <div className={styles.profileMenu}>
              <div className={styles.profileTrigger}>
                <div className={styles.profileAvatarFallback}>
                  {(user.name || user.email || 'U').charAt(0).toUpperCase()}
                </div>
                <div className={styles.profileCopy}>
                  <div className={styles.profileName}>{user.name || user.email}</div>
                  <div className={styles.profileHint}>Tài khoản</div>
                </div>
              </div>
            </div>
          ) : (
            <>
              <Link to="/login" className={styles.loginLink}>
                Đăng nhập
              </Link>
              <Link to="/register" className={styles.proButton}>
                Đăng ký
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;