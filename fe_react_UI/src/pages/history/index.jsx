import { useEffect, useMemo, useState } from "react";

import { useAuth } from "@/contexts/AuthContext";
import { getHistory } from "@/services/apiService";

import { exportMultipleHistoriesToZip } from "@/utils/pdfExport";
import HistoryItem from "@/components/History/HistoryItem";
import HistoryDetailsModal from "@/components/History/HistoryDetailsModal";

import styles from "./History.module.css";

const getChangedTime = (item) => {
  const value = new Date(item?.changed_at).getTime();
  return Number.isFinite(value) ? value : 0;
};

const stripHtml = (html = "") =>
  html
    .replace(/<[^>]*>/g, "")
    .replace(/\s+/g, " ")
    .trim();

const normalizeTitle = (value = "") =>
  stripHtml(value).normalize("NFC").toLowerCase();

const getPromptTitles = (prompt) => {
  if (!prompt) return [];

  try {
    const parsedPrompt = JSON.parse(prompt);
    return (parsedPrompt?.diagnostics || [])
      .map((item) => item?.title)
      .filter(Boolean);
  } catch {
    return [];
  }
};

const splitGeneratedPosts = (item) => {
  const content = item?.content || "";
  const promptTitles = getPromptTitles(item?.prompt);

  if (promptTitles.length <= 1) {
    return [item];
  }

  const titleSet = new Set(promptTitles.map(normalizeTitle));
  const headingRegex = /<h2[^>]*>([\s\S]*?)<\/h2>/gi;
  const headings = Array.from(content.matchAll(headingRegex)).filter((heading) =>
    titleSet.has(normalizeTitle(heading[1]))
  );

  if (headings.length <= 1) {
    return [item];
  }

  return headings.map((heading, index) => {
    const start = heading.index + heading[0].length;
    const nextHeading = headings[index + 1];
    const end = nextHeading ? nextHeading.index : content.length;

    return {
      ...item,
      id: `${item.id}-${index}`,
      history_id: item.id,
      title: stripHtml(heading[1]) || item.title,
      content: content.slice(start, end).trim(),
    };
  });
};

const getUsageFromItem = (item) => ({
  inputTokens: Number(item?.input_tokens || 0),
  outputTokens: Number(item?.output_tokens || 0),
  creditCost: Number(item?.credit_cost || 0),
});

function History() {
  const { user } = useAuth();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [sortMode, setSortMode] = useState("newest");
  const [page, setPage] = useState(1);
  const [modalOpen, setModalOpen] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await getHistory();
        setHistory(data);
      } catch (error) {
        console.error("Error fetching history:", error);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchHistory();
    }
  }, [user]);

  const groupedHistory = useMemo(() => {
    const groups = new Map();

    history.forEach((item) => {
      const postId = item?.post_id || item?.id;
      if (!groups.has(postId)) {
        groups.set(postId, []);
      }
      groups.get(postId).push(...splitGeneratedPosts(item));
    });

    return Array.from(groups.values()).map((groupItems) => {
      const dates = groupItems.map(getChangedTime);
      const titles = groupItems.map((item) => item.title).filter(Boolean);
      return {
        postId: groupItems[0]?.post_id || groupItems[0]?.id,
        items: groupItems.sort((a, b) => getChangedTime(b) - getChangedTime(a)),
        earliestDate: new Date(Math.min(...dates)),
        latestDate: new Date(Math.max(...dates)),
        titles,
        usage: getUsageFromItem(groupItems[0]),
        searchText: `${titles.join(" ")} ${groupItems
          .map((item) => stripHtml(item.content || ""))
          .join(" ")}`.toLowerCase(),
      };
    });
  }, [history]);

  const visibleHistory = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return groupedHistory
      .filter((group) => (normalizedQuery ? group.searchText.includes(normalizedQuery) : true))
      .sort((a, b) => {
        if (sortMode === "oldest") {
          return new Date(a.latestDate).getTime() - new Date(b.latestDate).getTime();
        }
        if (sortMode === "mostPosts") {
          return b.items.length - a.items.length;
        }
        return new Date(b.latestDate).getTime() - new Date(a.latestDate).getTime();
      });
  }, [groupedHistory, query, sortMode]);

  useEffect(() => {
    setPage(1);
  }, [query, sortMode]);

  const pageSize = 12;
  const pageCount = Math.max(1, Math.ceil(visibleHistory.length / pageSize));
  const currentPage = Math.min(page, pageCount);
  const pagedHistory = visibleHistory.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const totalPosts = groupedHistory.reduce((sum, group) => sum + group.items.length, 0);

  const handleViewDetails = (group) => {
    setSelectedGroup(group);
    setModalOpen(true);
  };

  const handleExportFromModal = async (selectedItems) => {
    if (selectedItems.length === 0) return;

    try {
      await exportMultipleHistoriesToZip(selectedItems);
    } catch (error) {
      console.error("Export failed:", error);
    }
    setModalOpen(false);
  };

  return (
    <section className={styles.historyContainer}>
      <div className={styles.header}>
        <div>
          <div className={styles.kicker}>History</div>
          <h1>Lịch sử bài viết</h1>
          <p>Xem lại các bài đã tạo theo nhóm để so sánh nhanh chất lượng, cấu trúc và nội dung chỉ trong vài giây.</p>
        </div>
        <div className={styles.headerArt} aria-hidden="true">
          <div className={styles.paperIcon}>
            <span className={styles.materialIcon}>article</span>
          </div>
          <span className={styles.historyOrb}>
            <span className={styles.materialIcon}>history</span>
          </span>
        </div>
      </div>

      <div className={styles.toolbar}>
        <label className={styles.searchBox}>
          <span className={styles.toolIcon} aria-hidden="true">
            <span className={styles.materialIcon}>search</span>
          </span>
          <span>Tìm kiếm</span>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Tìm theo tiêu đề hoặc nội dung"
          />
        </label>
        <label className={styles.sortBox}>
          <span className={styles.toolIcon} aria-hidden="true">
            <span className={styles.materialIcon}>sort</span>
          </span>
          <span>Sắp xếp</span>
          <select value={sortMode} onChange={(event) => setSortMode(event.target.value)}>
            <option value="newest">Mới nhất</option>
            <option value="oldest">Cũ nhất</option>
            <option value="mostPosts">Nhiều bài nhất</option>
          </select>
        </label>
        <div className={styles.summaryCard}>
          <span className={styles.summaryIcon} aria-hidden="true">
            <span className={styles.materialIcon}>auto_stories</span>
          </span>
          <strong>{groupedHistory.length}</strong>
          <span>Lần tạo</span>
        </div>
        <div className={styles.summaryCard}>
          <span className={styles.summaryIcon} aria-hidden="true">
            <span className={styles.materialIcon}>description</span>
          </span>
          <strong>{totalPosts}</strong>
          <span>Bài viết</span>
        </div>
      </div>

      {loading ? (
        <div className={styles.loading}>Đang tải lịch sử...</div>
      ) : visibleHistory.length === 0 ? (
        <div className={styles.emptyState}>Chưa có bài viết nào được lưu trong lịch sử.</div>
      ) : (
        <>
          <div className={styles.historyList}>
            {pagedHistory.map((group) => (
              <HistoryItem
                key={group.postId}
                group={group}
                onViewDetails={() => handleViewDetails(group)}
              />
            ))}
          </div>

          {pageCount > 1 && (
            <nav className={styles.pagination} aria-label="Phân trang lịch sử">
              <button type="button" onClick={() => setPage((value) => Math.max(1, value - 1))} disabled={currentPage === 1}>
                ‹
              </button>
              {Array.from({ length: pageCount }).map((_, index) => {
                const pageNumber = index + 1;
                if (pageCount > 5 && pageNumber > 3 && pageNumber < pageCount) {
                  if (pageNumber === 4) return <span key="ellipsis">...</span>;
                  return null;
                }
                return (
                  <button
                    type="button"
                    key={pageNumber}
                    className={pageNumber === currentPage ? styles.pageActive : ""}
                    onClick={() => setPage(pageNumber)}
                  >
                    {pageNumber}
                  </button>
                );
              })}
              <button type="button" onClick={() => setPage((value) => Math.min(pageCount, value + 1))} disabled={currentPage === pageCount}>
                ›
              </button>
            </nav>
          )}
        </>
      )}

      <HistoryDetailsModal
        key={selectedGroup?.postId || "history-modal"}
        group={selectedGroup}
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onExport={handleExportFromModal}
      />
    </section>
  );
}

export default History;
