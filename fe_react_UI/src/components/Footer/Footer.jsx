import { Link } from "react-router-dom";
import logoWeb from "@/assets/logoweb.png";
import styles from "./Footer.module.css";

function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.footerContent}>
        <div className={styles.footerBrand}>
          <Link to="/" className={styles.brandLine} aria-label="Trang chủ Smomer">
            <span className={styles.brandMark}>
              <img src={logoWeb} alt="" />
            </span>
            <span>
              <strong>Smomer</strong>
              <em>Xưởng nội dung AI</em>
            </span>
          </Link>
          <h3>Xưởng nội dung AI cho đội ngũ cần tạo bài nhanh, rõ cấu trúc và kiểm soát chi phí.</h3>
          <p>Tạo bài hàng loạt, dự đoán credit, lưu lịch sử và theo dõi token trong cùng một hệ thống.</p>
        </div>

        <nav className={styles.footerSection} aria-label="Khám phá">
          <h4>Khám phá</h4>
          <a href="/#about">Giới thiệu</a>
          <a href="/#features">Tính năng</a>
          <a href="/#workflow">Quy trình</a>
        </nav>

        <nav className={styles.footerSection} aria-label="Sản phẩm">
          <h4>Sản phẩm</h4>
          <Link to="/create-post">Tạo bài</Link>
          <Link to="/plans">Credit</Link>
          <Link to="/history">Lịch sử</Link>
        </nav>
      </div>

      <div className={styles.footerBottom}>
        <p>© 2026 Smomer. Thiết kế cho quy trình nội dung hiện đại.</p>
      </div>
    </footer>
  );
}

export default Footer;
