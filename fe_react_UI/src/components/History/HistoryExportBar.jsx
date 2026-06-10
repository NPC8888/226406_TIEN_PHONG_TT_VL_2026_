import { useMemo } from "react";

import styles from "./HistoryExportBar.module.css";

function HistoryExportBar({
  history,
  selectedId,
  onSelectId,
  onExportSingle,
  exporting,
} = {}) {
  const selected = useMemo(
    () => (history || []).find((x) => x?.id === selectedId) || null,
    [history, selectedId]
  );

  return (
    <div className={styles.barWrap}>
      <div className={styles.bar}>
        <div className={styles.label}>Xuất PDF</div>

        <div className={styles.actions}>
          <button
            type="button"
            className={styles.btn}
            disabled={!selected || exporting}
            onClick={onExportSingle}
          >
            Xuất bài đã chọn
          </button>

          
        </div>

        <div className={styles.selectedMeta}>
          {selected ? (
            <span>
              Đang chọn: <strong>{selected.title || `Bài ${selected.id}`}</strong>
            </span>
          ) : (
            <span>Chưa chọn bài để xuất</span>
          )}
        </div>

        {selected && (
          <button type="button" className={styles.pickBtn} disabled={exporting} onClick={() => onSelectId?.(selected.id)}>
            Đặt lại chọn
          </button>
        )}
      </div>

      {/* picker row (optional but helps UX) */}
      {history?.length ? (
        <div className={styles.pickerRow}>
          <div className={styles.pickerLabel}>Chọn bài:</div>
          <div className={styles.pickerChips}>
            {history.slice(0, 12).map((it, i) => {
              const active = it?.id === selectedId;
              return (
                <button
                  key={it.id || i}
                  type="button"
                  className={active ? styles.chipActive : styles.chip}
                  onClick={() => onSelectId?.(it.id)}
                  disabled={exporting}
                >
                  {it.title ? it.title : `Bài ${i + 1}`}
                </button>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default HistoryExportBar;

