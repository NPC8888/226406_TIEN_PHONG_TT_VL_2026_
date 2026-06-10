import styles from "./HistoryItem.module.css";

function HistoryItem({ group, onViewDetails }) {
  const itemCount = group.items.length;
  const createdAt = new Date(group.latestDate || group.earliestDate).toLocaleString("vi-VN");
  const firstItem = group.items[0];
  const titles = group.titles?.length ? group.titles : group.items.map((item) => item.title).filter(Boolean);
  const usage = group.usage || {};

  return (
    <article className={styles.historyItem}>
      <div className={styles.cardTop}>
        <span className={styles.groupBadge}>
          <i aria-hidden="true" />
          {itemCount} {itemCount > 1 ? "bài trong nhóm" : "bài"}
        </span>
        <span className={styles.timeText}>{createdAt}</span>
      </div>

      <div className={styles.metaRow}>
        <span className={styles.metaText}>Trạng thái</span>
        <span className={styles.statusBadge}>{firstItem?.status || "-"}</span>
      </div>

      <div className={styles.metaRow}>
        <span className={styles.metaText}>
          In {Number(usage.inputTokens || 0).toLocaleString()} / Out {Number(usage.outputTokens || 0).toLocaleString()} tokens
        </span>
        <span className={styles.creditBadge}>{Number(usage.creditCost || 0).toFixed(6)} credit</span>
      </div>

      {titles.length > 0 && (
        <div className={styles.titleChips}>
          {titles.slice(0, 3).map((title, index) => (
            <span key={`${title}-${index}`}>{title}</span>
          ))}
          {titles.length > 3 && <span>+{titles.length - 3}</span>}
        </div>
      )}

      <button className={styles.viewDetailsBtn} onClick={onViewDetails} type="button">
        Xem chi tiết ({itemCount})
        <span aria-hidden="true">→</span>
      </button>
    </article>
  );
}

export default HistoryItem;
