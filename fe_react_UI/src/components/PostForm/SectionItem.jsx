function SectionItem({ index, section, onChange, onRemove, toRoman }) {
  return (
    <div className="section-item-card">
      <div className="section-item-header">
        <h6 className="section-item-title">📌 Mục {toRoman(index + 1)}</h6>
        <button type="button" className="btn btn-remove-section" onClick={() => onRemove(index)}>
          ✕
        </button>
      </div>

      <div className="section-item-body">
        <div className="mb-2">
          <label className="form-label section-label">Tên mục</label>
          <input
            type="text"
            className="form-control section-input"
            placeholder="VD: Giới thiệu"
            value={section.title}
            onChange={(e) => onChange(index, "title", e.target.value)}
          />
        </div>

        <div className="mb-2">
          <label className="form-label section-label">Mô tả</label>
          <textarea
            className="form-control section-input"
            rows={2}
            placeholder="VD: viết 150 từ..."
            value={section.desc}
            onChange={(e) => onChange(index, "desc", e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}

export default SectionItem;
