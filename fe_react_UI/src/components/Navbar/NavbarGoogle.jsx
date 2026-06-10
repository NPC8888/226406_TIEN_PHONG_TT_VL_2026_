import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { useAuth } from "@/contexts/AuthContext";
import logoWeb from "@/assets/logoweb.png";

import styles from "./Navbar.module.css";

function NavbarGoogle() {
  const { user, logout, activeSubscription } = useAuth();
  const location = useLocation();
  const isHome = location.pathname === "/";
  const [menuOpen, setMenuOpen] = useState(false);
  const profileMenuRef = useRef(null);
  const creditBalance = Number(activeSubscription?.credit_balance ?? user?.credit_balance ?? 0);

  const navItems = [
    { label: "Giới thiệu", href: "/#about", active: isHome },
    ...(user ? [{ label: "Lịch sử", to: "/history", active: location.pathname === "/history" }] : []),
    { label: "Tạo bài", to: "/create-post", active: location.pathname === "/create-post" },
    ...(user?.role === "admin" ? [{ label: "Admin", to: "/admin", active: location.pathname === "/admin" }] : []),
  ];

  const displayName = useMemo(() => user?.name || user?.email || "Tài khoản", [user]);
  const avatarFallback = useMemo(() => (displayName || "T").trim().charAt(0).toUpperCase(), [displayName]);

  useEffect(() => {
    if (!menuOpen) return undefined;

    const handlePointerDown = (event) => {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    };

    const handleEscape = (event) => {
      if (event.key === "Escape") setMenuOpen(false);
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [menuOpen]);

  return (
    <nav className={styles.navbar}>
      <div className={styles.navInner}>
        <Link to="/" className={styles.brandArea} aria-label="Trang chủ Smomer">
          <span className={styles.brandMarkWrap}>
            <img className={styles.brandMark} src={logoWeb} alt="" />
          </span>
          <span className={styles.brandCopy}>
            <span className={styles.brandLogo}>Smomer</span>
            <span className={styles.brandTag}>Xưởng nội dung AI</span>
          </span>
        </Link>

        <div className={styles.navLinks} aria-label="Dieu huong chinh">
          {navItems.map((item) =>
            item.to ? (
              <Link key={item.label} to={item.to} className={`${styles.navLink} ${item.active ? styles.navLinkActive : ""}`}>
                {item.label}
              </Link>
            ) : (
              <a key={item.label} href={item.href} className={`${styles.navLink} ${item.active ? styles.navLinkActive : ""}`}>
                {item.label}
              </a>
            ),
          )}
        </div>

        <div className={styles.actionsArea}>
          {user ? (
            <>
              <Link to="/plans" className={styles.creditPill} title="Số credit hiện có">
                <span>{creditBalance.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>
                <em>CREDIT</em>
              </Link>
              <div className={styles.profileMenu} ref={profileMenuRef}>
                <button
                  type="button"
                  className={styles.profileTrigger}
                  onClick={() => setMenuOpen((current) => !current)}
                  aria-haspopup="menu"
                  aria-expanded={menuOpen}
                >
                  {user.avatar_url ? (
                    <img className={styles.profileAvatar} src={user.avatar_url} alt={displayName} />
                  ) : (
                    <span className={styles.profileAvatarFallback}>{avatarFallback}</span>
                  )}
                  <span className={styles.profileCopy}>
                    <span className={styles.profileName}>{displayName}</span>
                    <span className={styles.profileHint}>Tài khoản</span>
                  </span>
                <span className={styles.profileChevron}>{menuOpen ? "⌃" : "⌄"}</span>
                </button>

                {menuOpen && (
                  <div className={styles.profileDropdown} role="menu">
                    <div className={styles.profileDropdownHeader}>
                      <div className={styles.profileDropdownName}>{displayName}</div>
                      {user.email && <div className={styles.profileDropdownEmail}>{user.email}</div>}
                    </div>
                    <Link className={styles.profileDropdownLink} to="/plans" onClick={() => setMenuOpen(false)}>
                      Nạp credit
                    </Link>
                    <Link className={styles.profileDropdownLink} to="/history" onClick={() => setMenuOpen(false)}>
                      Lịch sử bài viết
                    </Link>
                    <button
                      className={styles.profileDropdownAction}
                      type="button"
                      onClick={() => {
                        setMenuOpen(false);
                        logout();
                      }}
                    >
                      Đăng xuất
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Link to="/login" state={!isHome ? { from: location } : undefined} className={styles.loginLink}>
                Đăng nhập
              </Link>
              <Link to="/login" className={styles.proButton}>
                Bắt đầu miễn phí
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

export default NavbarGoogle;
