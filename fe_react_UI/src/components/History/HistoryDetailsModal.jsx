import { useState } from "react";
import styles from "./HistoryDetailsModal.module.css";

function stripHtml(html) {
  if (!html || typeof document === "undefined") return "";
  const element = document.createElement("div");
  element.innerHTML = html;
  return (element.textContent || "").replace(/\s+/g, " ").trim();
}

function HistoryDetailsModal({ group, isOpen, onClose, onExport }) {
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [activeIndex, setActiveIndex] = useState(0);

  const items = group?.items || [];
  const activeItem = items[activeIndex] || items[0];
  const allSelected = selectedIds.size === items.length && items.length > 0;
  const someSelected = selectedIds.size > 0;

  if (!isOpen || !group) return null;

  const handleToggleItem = (itemId) => {
    setSelectedIds((current) => {
      const nextSelection = new Set(current);
      if (nextSelection.has(itemId)) {
        nextSelection.delete(itemId);
      } else {
        nextSelection.add(itemId);
      }
      return nextSelection;
    });
  };

  const handleSelectAll = () => {
    setSelectedIds(allSelected ? new Set() : new Set(items.map((item) => item.id)));
  };

  const handleExport = async () => {
    const selectedItems = items.filter((item) => selectedIds.has(item.id));
    if (selectedItems.length === 0) return;
    await onExport(selectedItems);
  };

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modal} onClick={(event) => event.stopPropagation()}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.title}>Chi tiết lần tạo ({items.length})</h2>
            <p className={styles.subtitle}>
              Từ {new Date(group.earliestDate).toLocaleString("vi-VN")} đến{" "}
              {new Date(group.latestDate).toLocaleString("vi-VN")}
            </p>
          </div>
          <button className={styles.closeBtn} onClick={onClose} aria-label="Đóng modal" type="button">
            x
          </button>
        </div>

        <div className={styles.contentGrid}>
          <div className={styles.itemsList}>
            {items.map((item, index) => {
              const isSelected = selectedIds.has(item.id);
              const contentPreview = stripHtml(item.content).substring(0, 150);

              return (
                <div
                  key={item.id}
                  className={`${styles.listItem} ${isSelected ? styles.listItemSelected : ""} ${
                    activeIndex === index ? styles.listItemActive : ""
                  }`}
                >
                  <input
                    type="checkbox"
                    id={`item-${item.id}`}
                    className={styles.checkbox}
                    checked={isSelected}
                    onChange={() => handleToggleItem(item.id)}
                  />
                  <button type="button" className={styles.itemContent} onClick={() => setActiveIndex(index)}>
                    <div className={styles.itemHeader}>
                      <span className={styles.itemBadge}>Bài {index + 1}</span>
                      {item.status && <span className={styles.itemStatus}>{item.status}</span>}
                    </div>
                    <h3 className={styles.itemTitle}>{item.title || `Bài ${index + 1}`}</h3>
                    {contentPreview && (
                      <p className={styles.itemPreview}>
                        {contentPreview}
                        {contentPreview.length >= 150 ? "..." : ""}
                      </p>
                    )}
                  </button>
                </div>
              );
            })}
          </div>

          <div className={styles.readerPane}>
            {activeItem && (
              <>
                <div className={styles.readerHeader}>
                  <div>
                    <span className={styles.itemBadge}>Bài {activeIndex + 1}</span>
                    <h3>{activeItem.title || `Bài ${activeIndex + 1}`}</h3>
                  </div>
                  <div className={styles.readerNav}>
                    <button
                      type="button"
                      onClick={() => setActiveIndex((current) => Math.max(0, current - 1))}
                      disabled={activeIndex === 0}
                    >
                      Trước
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveIndex((current) => Math.min(items.length - 1, current + 1))}
                      disabled={activeIndex >= items.length - 1}
                    >
                      Sau
                    </button>
                  </div>
                </div>
                <div className={styles.readerBody} dangerouslySetInnerHTML={{ __html: activeItem.content || "" }} />
              </>
            )}
          </div>
        </div>

        <div className={styles.footer}>
          <div className={styles.footerLeft}>
            <button className={styles.selectBtn} onClick={handleSelectAll} type="button">
              {allSelected ? "Bỏ chọn tất cả" : "Chọn tất cả"}
            </button>
            {someSelected && <span className={styles.selectedCount}>{selectedIds.size} được chọn</span>}
          </div>
          <div className={styles.footerRight}>
            <button className={styles.cancelBtn} onClick={onClose} type="button">
              Hủy
            </button>
            <button
              className={`${styles.exportBtn} ${!someSelected ? styles.exportBtnDisabled : ""}`}
              onClick={handleExport}
              disabled={!someSelected}
              type="button"
            >
              Xuất PDF ({selectedIds.size})
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HistoryDetailsModal;
