import { Link } from "react-router-dom";
import "./Home.css";

const benefits = [
  {
    icon: "doc",
    title: "Tạo bài hàng loạt",
    text: "Nhập nhiều tiêu đề, dùng chung một dàn ý và tạo từng bài riêng biệt trong cùng một lần chạy.",
  },
  {
    icon: "shield",
    title: "Kiểm soát chi phí",
    text: "Xem dự đoán credit trước khi tạo và theo dõi token input/output sau mỗi lần sinh nội dung.",
  },
  {
    icon: "calendar",
    title: "Lưu lịch sử rõ ràng",
    text: "Mỗi batch được lưu theo nhóm, dễ mở lại, so sánh, xuất file và kiểm tra lượng credit đã dùng.",
  },
];

const workflow = [
  { icon: "user", text: "Nhập danh sách tiêu đề và phong cách viết." },
  { icon: "spark", text: "Chọn hoặc để AI gợi ý cấu trúc bài viết." },
  { icon: "clock", text: "Xem dự đoán credit, sau đó tạo nội dung." },
  { icon: "briefcase", text: "Đọc lại, xuất file và theo dõi lịch sử sử dụng." },
];

function Home() {
  return (
    <main className="home-page">
      <section className="home-hero" id="about">
        <span className="home-sparkle home-sparkle-left">✦</span>
        <div className="home-hero-copy">
          <div className="home-kicker">Xưởng nội dung AI</div>
          <h1>Tạo nội dung hàng loạt mà vẫn kiểm soát được cấu trúc và chi phí.</h1>
          <p>
            Smomer giúp bạn biến danh sách ý tưởng thành các bài viết có dàn ý rõ ràng, đồng thời hiển thị
            credit ước tính và token đã sử dụng.
          </p>
          <div className="home-actions">
            <Link to="/create-post" className="home-primary-btn">
              <span>Bắt đầu tạo bài</span>
              <span aria-hidden="true">→</span>
            </Link>
            <Link to="/plans" className="home-secondary-btn">
              <span className="home-btn-icon" aria-hidden="true">▣</span>
              Xem credit
            </Link>
          </div>
        </div>
      </section>

      <section className="home-benefits" id="features">
        {benefits.map((item) => (
          <article key={item.title} className="home-benefit">
            <div className={`home-benefit-icon home-icon-${item.icon}`} aria-hidden="true">
              <span />
            </div>
            <div>
              <h2>{item.title}</h2>
              <p>{item.text}</p>
            </div>
            <span className="home-card-arrow" aria-hidden="true">→</span>
          </article>
        ))}
      </section>

      <section className="home-workflow" id="workflow">
        <div className="home-workflow-content">
          <div className="home-workflow-text">
            <div className="home-kicker">Quy trình</div>
            <h2>
              Một luồng làm việc gọn từ <span>ý tưởng</span> đến <span>bài viết</span> đã lưu.
            </h2>
            <div className="home-paper-illustration" aria-hidden="true">
              <div className="home-paper">
                <i />
                <i />
                <b />
                <b />
              </div>
              <div className="home-star-tile">✦</div>
              <span>✦</span>
            </div>
          </div>
          <div className="home-workflow-list">
            {workflow.map((item, index) => (
              <div key={item.text} className="home-workflow-row">
                <span className="home-workflow-number">{String(index + 1).padStart(2, "0")}</span>
                <div className="home-workflow-item">
                  <span className={`home-workflow-icon home-workflow-${item.icon}`} aria-hidden="true" />
                  <p>{item.text}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="home-cta">
        <div className="home-cta-content">
          <div>
            <h2>Điều hành nội dung bằng credit minh bạch.</h2>
            <p>Tài khoản mới có 1 credit miễn phí. Chi phí thực tế được tính theo token input/output sau khi tạo bài.</p>
          </div>
          <div className="home-cta-illustration" aria-hidden="true">
            <div className="home-credit-stack">
              <span />
              <span />
              <span />
            </div>
            <div className="home-credit-small-stack">
              <span />
              <span />
            </div>
            <i>✦</i>
          </div>
          <Link to="/create-post" className="home-primary-btn home-cta-btn">
            <span>Mở khu làm việc</span>
            <span aria-hidden="true">→</span>
          </Link>
        </div>
      </section>
    </main>
  );
}

export default Home;
