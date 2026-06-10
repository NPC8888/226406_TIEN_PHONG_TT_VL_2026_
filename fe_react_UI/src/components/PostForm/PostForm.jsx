import { useState } from "react";
import usePostBuilder from "./usePostBuilder";
import SectionItem from "./SectionItem";
import { generatePosts } from "../../services/apiService";

function PostForm() {
  const {
    titles,
    setTitles,
    style,
    setStyle,
    sections,
    // eslint-disable-next-line no-unused-vars
    payload,
    submitted,
    addSection,
    removeSection,
    updateSection,
    handleSubmit,
    resetBuilder,
    toRoman,
  } = usePostBuilder();
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const onSubmit = async () => {
    const data = handleSubmit();
    if (data) {
      setLoading(true);
      setError(null);
      try {
        // Send the payload directly to match backend PostCreate schema
        const response = await generatePosts(data);
        setPosts(response.data); // Access the data array from backend response
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="professional-form">
      <div className="form-card-wrapper">
        <div className="card shadow-lg border-0 form-card">
          <div className="card-body p-4">
            <div className="form-header mb-4">
              <h2 className="form-title">✨ Xây dựng Prompt Bài Viết</h2>
              <p className="form-subtitle">Tạo nội dung chất lượng với AI</p>
            </div>

            <div className="form-section mb-3">
              <h5 className="section-title">📝 Danh sách Tiêu đề</h5>
              <textarea
                className={`form-control form-input ${submitted && !titles.trim() ? "is-invalid" : ""}`}
                rows={3}
                placeholder="Nhập mỗi tiêu đề trên một dòng..."
                value={titles}
                onChange={(e) => setTitles(e.target.value)}
              />
              {submitted && !titles.trim() && (
                <div className="invalid-feedback">Hãy nhập ít nhất một tiêu đề.</div>
              )}
            </div>

            <div className="form-section mb-3">
              <h5 className="section-title">🎨 Phong cách Viết</h5>
              <input
                className="form-control form-input"
                placeholder="VD: chuyên nghiệp, marketing, sáng tạo..."
                value={style}
                onChange={(e) => setStyle(e.target.value)}
              />
            </div>

            <div className="form-section mb-3">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <h5 className="section-title mb-0">📋 Cấu trúc Bài viết</h5>
                <button type="button" className="btn btn-add-section" onClick={addSection}>
                  ➕ Thêm Mục
                </button>
              </div>

              <div className="sections-container">
                {sections.map((section, index) => (
                  <SectionItem
                    key={index}
                    index={index}
                    section={section}
                    onChange={updateSection}
                    onRemove={removeSection}
                    toRoman={toRoman}
                  />
                ))}
              </div>

              {submitted && sections.some((sec) => !sec.title.trim()) && (
                <div className="text-danger mt-2">Mỗi mục cần có tên mục đầy đủ.</div>
              )}
            </div>

            <div className="form-actions d-flex gap-2 justify-content-center">
              <button type="button" className="btn btn-generate" onClick={onSubmit} disabled={loading}>
                {loading ? "⏳ Đang Tạo..." : "🚀 Tạo Bài Viết"}
              </button>
              <button
                type="button"
                className="btn btn-reset"
                onClick={() => {
                  resetBuilder();
                  setPosts([]);
                  setError(null);
                }}
              >
                Đặt Lại
              </button>
            </div>

            {loading && (
              <div className="mt-3">
                <div className="alert alert-loading" role="alert">
                  <div className="spinner-border spinner-border-sm me-2" role="status"></div>
                  Đang tạo bài viết với AI...
                </div>
              </div>
            )}

            {error && (
              <div className="mt-3">
                <div className="alert alert-error" role="alert">
                  ❌ Lỗi: {error}
                </div>
              </div>
            )}

            {posts.length > 0 && (
              <div className="mt-4">
                <h5 className="results-title">📄 Bài Viết Đã Tạo</h5>
                <div className="posts-grid">
                  {posts.map((post, index) => (
                    <div key={index} className="post-card">
                      <div className="post-header">
                        <h6 className="post-title">{post.title || `Bài viết ${index + 1}`}</h6>
                      </div>
                      <div
                        className="post-content post-html"
                        dangerouslySetInnerHTML={{ __html: post.content || post.body }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default PostForm;
