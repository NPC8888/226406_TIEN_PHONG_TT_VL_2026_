import styles from "./PostFormModern.module.css";

function SectionEditorCard({ index, section, onChange, onRemove, canRemove, isOpen, onToggle }) {
  const wordCountError = section.word_count && Number(section.word_count) < 50;

  return (
    <div className={`${styles.fieldCard} ${styles.sectionCard} ${!isOpen ? styles.sectionCardCompact : ""}`}>
      <div className={`${styles.sectionHeader} ${styles.sectionCardHeader}`}>
        <div className={styles.sectionSummary}>
          <div className={styles.outlineIndex}>{index + 1}</div>
          <div>
            <h3 className={styles.sectionTitle}>{section.title || `Mục ${index + 1}`}</h3>
            {!isOpen && (
              <p className={styles.sectionCompactMeta}>
                {section.word_count || 0} từ - {section.role || "Chưa có vai trò"}
              </p>
            )}
          </div>
        </div>
        <div className={styles.sectionCardActions}>
          <button type="button" className={styles.buttonGlassSmall} onClick={onToggle}>
            {isOpen ? "Thu gọn" : "Sửa"}
          </button>
          {canRemove && (
            <button type="button" className={`${styles.buttonDanger} ${styles.sectionRemoveButton}`} onClick={() => onRemove(index)}>
              Xóa
            </button>
          )}
        </div>
      </div>

      {!isOpen && <p className={styles.sectionCompactDesc}>{section.description || "Chưa có mô tả mục."}</p>}

      {isOpen && (
        <div className={styles.sectionEditPanel}>
          <div className={styles.sectionEditTop}>
            <label className={styles.compactField}>
              <span>Tên mục</span>
              <input
                type="text"
                className={styles.input}
                value={section.title}
                placeholder="Ví dụ: Mở đầu, Vấn đề, Giải pháp"
                onChange={(event) => onChange(index, "title", event.target.value)}
              />
            </label>

            <label className={styles.compactField}>
              <span>Số từ</span>
              <input
                type="number"
                min="50"
                step="10"
                className={`${styles.numberInput} ${wordCountError ? styles.inputErrorSoft : ""}`}
                value={section.word_count}
                placeholder="250"
                onChange={(event) => onChange(index, "word_count", event.target.value)}
              />
            </label>
          </div>

          <label className={styles.compactField}>
            <span>Vai trò / luật viết</span>
            <textarea
              className={`${styles.textarea} ${styles.compactTextarea}`}
              value={section.role}
              placeholder="Viết như chuyên gia, tập trung vào lợi ích chính, tránh liệt kê dài..."
              onChange={(event) => onChange(index, "role", event.target.value)}
            />
          </label>

          <label className={styles.compactField}>
            <span>Mô tả mục</span>
            <textarea
              className={`${styles.textarea} ${styles.compactTextarea}`}
              value={section.description}
              placeholder="Ý chính, insight cần đưa vào và điều mục này phải truyền tải."
              onChange={(event) => onChange(index, "description", event.target.value)}
            />
          </label>

          <div className={styles.sectionEditHint}>Các mục còn trống sẽ được nhắc khi bạn bấm tạo bài viết.</div>
        </div>
      )}
    </div>
  );
}

export default SectionEditorCard;
