import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";

import { estimateGeneratePosts, generatePosts, suggestSectionOutlines, suggestWritingStyles } from "@/services/apiService";
import { useAuth } from "@/contexts/AuthContext";

import SectionEditorCard from "./SectionEditorCard";
import usePostComposer from "./usePostComposer";
import styles from "./PostFormModern.module.css";

const splitTags = (value) =>
  value
    .split(/[\n,]+/)
    .map((item) => item.trim().normalize("NFC"))
    .filter(Boolean);

const uniqueTags = (items) => Array.from(new Set(items));

function ModalPortal({ children }) {
  if (typeof document === "undefined") {
    return children;
  }

  return createPortal(children, document.body);
}

function SuggestIcon({ loading = false }) {
  return (
    <span className={`${styles.suggestIcon} ${loading ? styles.suggestIconLoading : ""}`} aria-hidden="true">
      {loading ? "" : "auto_fix_high"}
    </span>
  );
}

function TagInput({
  label,
  value,
  draft,
  placeholder,
  error,
  suggestions = [],
  isSuggesting = false,
  showSuggestions = false,
  onSuggest,
  onCloseSuggestions,
  onDraftChange,
  onChange,
}) {
  const tags = useMemo(() => uniqueTags(splitTags(value)), [value]);

  const commitTags = (items) => {
    onChange(uniqueTags(items).join("\n"));
  };

  const addDraft = () => {
    const next = splitTags(draft);
    if (!next.length) return;
    commitTags([...tags, ...next]);
    onDraftChange("");
  };

  const removeTag = (tag) => {
    commitTags(tags.filter((item) => item !== tag));
  };

  const addSuggestion = (suggestion) => {
    commitTags([...tags, suggestion]);
    onCloseSuggestions?.();
  };

  return (
    <div className={styles.label}>
      <span className={styles.labelText}>{label}</span>
      <div className={styles.tagInputWrap}>
        <div className={`${styles.tagBox} ${error ? styles.inputError : ""}`}>
          {tags.map((tag) => (
            <span key={tag} className={styles.tagNode}>
              <span>{tag}</span>
              <button type="button" className={styles.tagRemove} onClick={() => removeTag(tag)} aria-label={`Xóa ${tag}`}>
                x
              </button>
            </span>
          ))}
          <input
            type="text"
            className={styles.tagInput}
            value={draft}
            placeholder={tags.length ? "Nhập thêm rồi bấm phẩy" : placeholder}
            onBlur={addDraft}
            onChange={(event) => {
              const nextValue = event.target.value;
              if (/[,\n]/.test(nextValue)) {
                commitTags([...tags, ...splitTags(nextValue)]);
                onDraftChange("");
                return;
              }
              onDraftChange(nextValue);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === "Tab") {
                event.preventDefault();
                addDraft();
              }
              if (event.key === "Backspace" && !draft && tags.length) {
                removeTag(tags[tags.length - 1]);
              }
            }}
          />
        </div>
        {onSuggest && (
          <button
            type="button"
            className={styles.suggestButton}
            onMouseDown={(event) => event.preventDefault()}
            onClick={onSuggest}
            disabled={isSuggesting}
            title="Gợi ý phong cách viết bằng AI"
            aria-label="Gợi ý phong cách viết bằng AI"
          >
            <SuggestIcon loading={isSuggesting} />
          </button>
        )}
      </div>

      {showSuggestions && (suggestions.length > 0 || isSuggesting) && (
        <div className={styles.suggestionPanel}>
          <div className={styles.suggestionHeader}>
            <span>Gợi ý phong cách viết</span>
            <div className={styles.suggestionHeaderActions}>
              {isSuggesting && <span className={styles.suggestionLoading}>Đang hỏi AI...</span>}
              <button type="button" className={styles.suggestionClose} onClick={onCloseSuggestions} aria-label="Đóng gợi ý">
                x
              </button>
            </div>
          </div>
          <div className={styles.suggestionChips}>
            {suggestions.map((suggestion) => (
              <button
                type="button"
                key={suggestion}
                className={styles.suggestionChip}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => addSuggestion(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function InfoHint({ text }) {
  return (
    <span className={styles.infoHint} tabIndex={0} aria-label={text}>
      i
      <span className={styles.infoTooltip}>{text}</span>
    </span>
  );
}

function OutlineSuggestionModal({
  open,
  description,
  layouts,
  loading,
  onDescriptionChange,
  onGenerate,
  onSelect,
  onClose,
}) {
  if (!open) return null;

  return (
    <div className={styles.modalOverlay} role="dialog" aria-modal="true" aria-label="Gợi ý cấu trúc bài viết">
      <div className={styles.outlineModal}>
        <div className={styles.modalHeader}>
          <div>
            <div className={styles.kicker}>Gợi ý dàn ý</div>
            <h2 className={styles.modalTitle}>
              Chọn bố cục bài viết
              <InfoHint text="Thêm mô tả nếu muốn AI bám sát hướng triển khai hơn." />
            </h2>
          </div>
          <button type="button" className={styles.modalClose} onClick={onClose} aria-label="Đóng cửa sổ">
            x
          </button>
        </div>

        <label className={styles.label}>
          <span className={styles.labelText}>Mô tả thêm cho AI</span>
          <textarea
            className={`${styles.textarea} ${styles.outlineBriefInput}`}
            value={description}
            placeholder="Ví dụ: bài dành cho chủ shop mới bắt đầu, ưu tiên thực tế, tránh thuật ngữ quá khó..."
            onChange={(event) => onDescriptionChange(event.target.value)}
          />
        </label>

        <div className={styles.modalActions}>
          <button type="button" className={styles.buttonPrimary} onClick={onGenerate} disabled={loading}>
            {loading ? "Đang gợi ý..." : layouts.length ? "Gợi ý lại" : "Gợi ý bố cục"}
          </button>
          <button type="button" className={styles.buttonGhost} onClick={onClose} disabled={loading}>
            Đóng
          </button>
        </div>

        {layouts.length > 0 && (
          <div className={styles.layoutGrid}>
            {layouts.map((layout, index) => (
              <article key={`${layout.name}-${index}`} className={styles.layoutOption}>
                <div className={styles.layoutOptionTop}>
                  <span className={styles.resultBadge}>Bố cục {index + 1}</span>
                  <span className={styles.resultMeta}>{layout.sections?.length || 0} mục</span>
                </div>
                <h3 className={styles.layoutTitle}>{layout.name}</h3>
                <p className={styles.outlineDesc}>{layout.summary}</p>
                <div className={styles.layoutSections}>
                  {(layout.sections || []).map((section, sectionIndex) => (
                    <div key={`${section.title}-${sectionIndex}`} className={styles.layoutSectionMini}>
                      <span>{sectionIndex + 1}</span>
                      <strong>{section.title}</strong>
                      <em>{section.word_count} từ</em>
                    </div>
                  ))}
                </div>
                <button type="button" className={styles.buttonSecondary} onClick={() => onSelect(layout)}>
                  Chọn bố cục này
                </button>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function OutlinePreview({ sections, sampleTitle }) {
  const [expandedIndex, setExpandedIndex] = useState(null);

  return (
    <div className={styles.articlePreview}>
      <div className={styles.articlePreviewTitleTile}>
        <span>Bấm từng mục để xem chi tiết</span>
        <strong>{sampleTitle || "Tiêu đề bài viết sẽ hiển thị ở đây"}</strong>
      </div>

      <div className={styles.articlePreviewSections}>
        {sections.map((section, index) => {
          const wordCount = Number(section.word_count) || 0;
          const lineCount = Math.max(1, Math.min(3, Math.ceil(wordCount / 220)));
          const expanded = expandedIndex === index;

          return (
            <button
              type="button"
              key={`preview-${index}`}
              className={`${styles.previewSectionTile} ${expanded ? styles.previewSectionTileOpen : ""}`}
              onClick={() => setExpandedIndex(expanded ? null : index)}
            >
              <div className={styles.previewSectionTop}>
                <span>{index + 1}</span>
                <strong>{section.title || "Mục chưa đặt tên"}</strong>
                <em>{wordCount || 0} từ</em>
              </div>

              <div className={styles.previewTextSkeleton} aria-hidden="true">
                {Array.from({ length: lineCount }).map((_, lineIndex) => (
                  <i
                    key={`line-${index}-${lineIndex}`}
                    style={{
                      width: `${lineIndex === lineCount - 1 ? 46 : 74 - (lineIndex % 2) * 12}%`,
                    }}
                  />
                ))}
              </div>

              {expanded && (
                <div className={styles.previewSectionDetails}>
                  <p>
                    <strong>Vai trò:</strong> {section.role || "Chưa có vai trò"}
                  </p>
                  <p>
                    <strong>Mô tả:</strong> {section.description || "Chưa có mô tả."}
                  </p>
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function stripHtml(html) {
  if (!html) return "";
  if (typeof window === "undefined") return "";
  const element = document.createElement("div");
  element.innerHTML = html;
  return (element.textContent || "").replace(/\s+/g, " ").trim();
}

function ResultsPanel({ posts }) {
  const [activePostIndex, setActivePostIndex] = useState(null);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedIndexes, setSelectedIndexes] = useState([]);
  const [compareOpen, setCompareOpen] = useState(false);

  const toggleSelected = (index) => {
    setSelectedIndexes((current) => (current.includes(index) ? current.filter((item) => item !== index) : [...current, index]));
  };

  const selectedPosts = selectedIndexes.map((index) => ({ ...posts[index], originalIndex: index })).filter(Boolean);
  const activePost = activePostIndex === null ? null : posts[activePostIndex];

  return (
    <section className={`${styles.resultsPanel} ${styles.resultsPanelReady}`}>
      <div className={styles.resultsHeader}>
        <div>
          <h2 className={styles.sectionTitle}>
            Kết quả sinh nội dung
            <InfoHint text={`${posts.length} bài đã tạo. Mở từng bài để đọc chi tiết hoặc chọn vài bài để so sánh.`} />
          </h2>
        </div>
        <div className={styles.resultsToolbar}>
          <button
            type="button"
            className={compareMode ? styles.buttonPrimary : styles.buttonSecondary}
            onClick={() => {
              setCompareMode((current) => !current);
              setSelectedIndexes([]);
            }}
          >
            {compareMode ? "Đang chọn so sánh" : "So sánh bài viết"}
          </button>
          {compareMode && (
            <button
              type="button"
              className={styles.buttonGhost}
              onClick={() => setCompareOpen(true)}
              disabled={selectedIndexes.length < 2}
            >
              Xem {selectedIndexes.length} bài
            </button>
          )}
        </div>
      </div>

      <div className={styles.resultsList}>
        {posts.map((post, index) => {
          const textPreview = stripHtml(post.content || post.body);
          const selected = selectedIndexes.includes(index);

          return (
            <article
              key={`${post.title}-${index}`}
              className={`${styles.resultListItem} ${styles.resultListItemFresh} ${selected ? styles.resultListItemSelected : ""}`}
              style={{ "--result-delay": `${Math.min(index * 90, 540)}ms` }}
            >
              {compareMode && (
                <label className={styles.compareCheck}>
                  <input type="checkbox" checked={selected} onChange={() => toggleSelected(index)} />
                  <span>Chọn</span>
                </label>
              )}
              <button type="button" className={styles.resultListButton} onClick={() => setActivePostIndex(index)}>
                <span className={styles.resultBadge}>Bài {index + 1}</span>
                <span className={styles.resultListCopy}>
                  <strong>{post.title || `Bài viết ${index + 1}`}</strong>
                  <em>{textPreview || "Nội dung đã được tạo."}</em>
                </span>
                <span className={styles.resultOpenHint}>Mở</span>
              </button>
            </article>
          );
        })}
      </div>

      {activePost && (
        <ModalPortal>
          <ResultReaderModal
            post={activePost}
            index={activePostIndex}
            onClose={() => setActivePostIndex(null)}
            onPrev={() => setActivePostIndex((current) => Math.max(0, current - 1))}
            onNext={() => setActivePostIndex((current) => Math.min(posts.length - 1, current + 1))}
            canPrev={activePostIndex > 0}
            canNext={activePostIndex < posts.length - 1}
          />
        </ModalPortal>
      )}

      {compareOpen && (
        <ModalPortal>
          <CompareModal posts={selectedPosts} onClose={() => setCompareOpen(false)} />
        </ModalPortal>
      )}
    </section>
  );
}

function ResultReaderModal({ post, index, onClose, onPrev, onNext, canPrev, canNext }) {
  return (
    <div className={styles.modalOverlay} role="dialog" aria-modal="true" aria-label="Chi tiết bài viết">
      <div className={styles.readerModal}>
        <div className={styles.readerHeader}>
          <div>
            <span className={styles.resultBadge}>Bài {index + 1}</span>
            <h2 className={styles.readerTitle}>{post.title || `Bài viết ${index + 1}`}</h2>
          </div>
          <button type="button" className={styles.modalClose} onClick={onClose} aria-label="Đóng chi tiết">
            x
          </button>
        </div>
        <div className={styles.readerBody}>
          <div className={styles.resultBody} dangerouslySetInnerHTML={{ __html: post.content || post.body }} />
        </div>
        <div className={styles.readerFooter}>
          <button type="button" className={styles.buttonGhost} onClick={onPrev} disabled={!canPrev}>
            Bài trước
          </button>
          <button type="button" className={styles.buttonGhost} onClick={onNext} disabled={!canNext}>
            Bài sau
          </button>
        </div>
      </div>
    </div>
  );
}

function CompareModal({ posts, onClose }) {
  return (
    <div className={styles.modalOverlay} role="dialog" aria-modal="true" aria-label="So sánh bài viết">
      <div className={styles.compareModal}>
        <div className={styles.readerHeader}>
          <div>
            <div className={styles.kicker}>So sánh</div>
            <h2 className={styles.readerTitle}>So sánh {posts.length} bài viết</h2>
          </div>
          <button type="button" className={styles.modalClose} onClick={onClose} aria-label="Đóng so sánh">
            x
          </button>
        </div>
        <div className={styles.compareGrid} style={{ "--compare-count": posts.length }}>
          {posts.map((post) => (
            <article key={`${post.title}-${post.originalIndex}`} className={styles.compareColumn}>
              <div className={styles.compareColumnHeader}>
                <span className={styles.resultBadge}>Bài {post.originalIndex + 1}</span>
                <h3>{post.title || `Bài viết ${post.originalIndex + 1}`}</h3>
              </div>
              <div className={styles.compareColumnBody}>
                <div className={styles.resultBody} dangerouslySetInnerHTML={{ __html: post.content || post.body }} />
              </div>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}

function PostFormModern() {
  const { user, activeSubscription, refreshProfile, refreshSubscription } = useAuth();
  const {
    titles,
    setTitles,
    style,
    setStyle,
    sections,
    submitted,
    normalizedTitles,
    addSection,
    removeSection,
    updateSection,
    replaceSections,
    handleSubmit,
    resetBuilder,
  } = usePostComposer();
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [titleDraft, setTitleDraft] = useState("");
  const [styleDraft, setStyleDraft] = useState("");
  const [styleSuggestions, setStyleSuggestions] = useState([]);
  const [suggestingStyles, setSuggestingStyles] = useState(false);
  const [showStyleSuggestions, setShowStyleSuggestions] = useState(false);
  const [outlineModalOpen, setOutlineModalOpen] = useState(false);
  const [outlineDescription, setOutlineDescription] = useState("");
  const [outlineLayouts, setOutlineLayouts] = useState([]);
  const [suggestingOutlines, setSuggestingOutlines] = useState(false);
  const [openSectionIndex, setOpenSectionIndex] = useState(-1);
  const [estimate, setEstimate] = useState(null);
  const [estimating, setEstimating] = useState(false);

  const titleTags = useMemo(() => uniqueTags([...normalizedTitles, ...splitTags(titleDraft)]), [normalizedTitles, titleDraft]);
  const styleTags = useMemo(() => uniqueTags([...splitTags(style), ...splitTags(styleDraft)]), [style, styleDraft]);

  const commitDraftInputs = () => {
    const nextTitles = titleTags;
    const nextStyle = styleTags.join(", ");
    setTitles(nextTitles.join("\n"));
    setStyle(nextStyle);
    return { nextTitles, nextStyle };
  };

  const buildGenerationPayload = (nextTitles = titleTags, nextStyle = styleTags.join(", ")) => {
    const payload = {
      titles: nextTitles,
      style: nextStyle.trim(),
      sections: sections.map((section) => ({
        title: (section.title || "").trim(),
        role: (section.role || "").trim(),
        word_count: Number(section.word_count),
        description: (section.description || "").trim(),
      })),
    };

    const isValid =
      payload.titles.length > 0 &&
      payload.style &&
      payload.sections.every(
        (section) =>
          section.title &&
          section.role &&
          section.description &&
          Number.isFinite(section.word_count) &&
          section.word_count >= 50,
      );

    return isValid ? payload : null;
  };

  useEffect(() => {
    const payload = buildGenerationPayload();
    if (!user || !payload || loading) {
      setEstimate(null);
      setEstimating(false);
      return undefined;
    }

    let cancelled = false;
    const timer = window.setTimeout(async () => {
      setEstimating(true);
      try {
        const response = await estimateGeneratePosts(payload);
        if (!cancelled) {
          setEstimate(response);
        }
      } catch {
        if (!cancelled) {
          setEstimate(null);
        }
      } finally {
        if (!cancelled) {
          setEstimating(false);
        }
      }
    }, 650);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [user, titleTags, styleTags, sections, loading]);

  const loadStyleSuggestions = async () => {
    if (!titleTags.length || titleTags.join(" ").length < 3) {
      setStyleSuggestions([]);
      setError("Nhập ít nhất một tiêu đề trước khi gợi ý phong cách viết.");
      return;
    }

    setShowStyleSuggestions(true);
    setSuggestingStyles(true);
    setError(null);
    try {
      const response = await suggestWritingStyles({ titles: titleTags });
      setStyleSuggestions(response.suggestions || []);
    } catch (requestError) {
      setStyleSuggestions([]);
      setError(requestError.message || "Không thể gợi ý phong cách viết.");
    } finally {
      setSuggestingStyles(false);
    }
  };

  const openOutlineSuggestions = () => {
    const { nextTitles, nextStyle } = commitDraftInputs();
    if (!nextTitles.length || !nextStyle) {
      setError("Nhập tiêu đề và phong cách viết trước khi gợi ý cấu trúc bài viết.");
      return;
    }
    setError(null);
    setOutlineModalOpen(true);
    if (!outlineLayouts.length) {
      loadOutlineSuggestions(nextTitles, nextStyle);
    }
  };

  const loadOutlineSuggestions = async (forcedTitles = titleTags, forcedStyle = styleTags.join(", ")) => {
    const titlesForRequest = forcedTitles.length ? forcedTitles : titleTags;
    const styleForRequest = forcedStyle || styleTags.join(", ");
    if (!titlesForRequest.length || !styleForRequest) {
      setError("Nhập tiêu đề và phong cách viết trước khi gợi ý cấu trúc bài viết.");
      return;
    }

    setSuggestingOutlines(true);
    setError(null);
    try {
      const response = await suggestSectionOutlines({
        titles: titlesForRequest,
        style: styleForRequest,
        description: outlineDescription,
      });
      setOutlineLayouts(response.layouts || []);
    } catch (requestError) {
      setOutlineLayouts([]);
      setError(requestError.message || "Không thể gợi ý cấu trúc bài viết.");
    } finally {
      setSuggestingOutlines(false);
    }
  };

  const selectOutlineLayout = (layout) => {
    replaceSections(layout.sections || []);
    setOpenSectionIndex(0);
    setOutlineModalOpen(false);
  };

  const submit = async () => {
    const { nextTitles, nextStyle } = commitDraftInputs();

    const data = handleSubmit({
      titles: nextTitles,
      style: nextStyle,
    });
    if (!data) {
      setError("Vui lòng hoàn thành đầy đủ tiêu đề, phong cách viết và mô tả cho từng mục.");
      return;
    }

    setLoading(true);
    setError(null);
    setEstimate(null);

    try {
      const estimateResponse = await estimateGeneratePosts(data);
      setEstimate(estimateResponse);
      if (!estimateResponse.has_enough_credits) {
        setError(
          `Không đủ credit. Dự đoán cần ${Number(estimateResponse.credit_cost).toFixed(6)} credit, hiện có ${Number(estimateResponse.credit_balance).toFixed(6)} credit.`
        );
        return;
      }
      const response = await generatePosts(data);
      setPosts(response.data || []);
      await refreshProfile();
      await refreshSubscription();
      if (response.usage) {
        setEstimate({
          input_tokens: response.usage.input_tokens,
          output_tokens: response.usage.output_tokens,
          total_tokens: response.usage.total_tokens,
          credit_cost: response.usage.credit_cost,
          credit_balance: response.usage.credit_balance,
          has_enough_credits: true,
          model: response.usage.model || estimateResponse.model,
        });
      }
    } catch (requestError) {
      setError(requestError.message || "Không thể tạo bài viết.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.shell}>
      <section className={styles.workspace} id="workspace">
        <div className={styles.workspaceHeader}>
          <div className={styles.workspaceTitleBlock}>
            <div className={styles.workspaceKickerCentered}>Khu làm việc</div>
            <span className={styles.workspaceUnderline} aria-hidden="true" />
          </div>
          <div className={styles.workspacePromptPill}>
            <span aria-hidden="true">✦</span>
            Tạo nội dung chất lượng, nhanh chóng và sáng tạo cùng AI
          </div>
        </div>

        <div className={styles.createGrid}>
          <div className={styles.createMain}>
            <div className={styles.fieldCard}>
              <div className={styles.fieldStack}>
                <div>
                  <h2 className={styles.sectionTitle}>
                    Thông tin tổng quan
                    <InfoHint text="Nhập danh sách tiêu đề cần viết và phong cách mong muốn. Bạn có thể thêm nhiều mục, chỉnh sửa hoặc xóa từng mục trước khi tạo bài." />
                  </h2>
                </div>

                <TagInput
                  label="Danh sách tiêu đề"
                  value={titles}
                  draft={titleDraft}
                  placeholder="Nhập thêm rồi bấm phẩy"
                  error={submitted && !titleTags.length}
                  onDraftChange={setTitleDraft}
                  onChange={setTitles}
                />

                <TagInput
                  label="Phong cách bài viết"
                  value={style}
                  draft={styleDraft}
                  placeholder="Nhập thêm rồi bấm phẩy"
                  error={submitted && !styleTags.length}
                  suggestions={styleSuggestions}
                  isSuggesting={suggestingStyles}
                  showSuggestions={showStyleSuggestions}
                  onSuggest={loadStyleSuggestions}
                  onCloseSuggestions={() => setShowStyleSuggestions(false)}
                  onDraftChange={setStyleDraft}
                  onChange={(nextValue) => setStyle(splitTags(nextValue).join(", "))}
                />
              </div>
            </div>

            <div className={styles.outlineCard}>
              <div className={styles.sectionHeader}>
                <div>
                  <h2 className={styles.sectionTitle}>
                    Cấu trúc bài viết
                    <InfoHint text="Gợi ý bố cục bằng AI, chọn một bố cục rồi mở từng mục để chỉnh thủ công." />
                  </h2>
                </div>
                <button type="button" className={styles.headerSuggestButton} onClick={openOutlineSuggestions} disabled={suggestingOutlines}>
                  <SuggestIcon loading={suggestingOutlines} />
                  {suggestingOutlines ? "Đang gợi ý..." : "Gợi ý cấu trúc"}
                </button>
              </div>

              <div className={styles.sectionsListCompact}>
                {sections.map((section, index) => (
                  <SectionEditorCard
                    key={`section-${index}`}
                    index={index}
                    section={section}
                    onChange={updateSection}
                    onRemove={(sectionIndex) => {
                      removeSection(sectionIndex);
                      setOpenSectionIndex(-1);
                    }}
                    canRemove={sections.length > 1}
                    isOpen={openSectionIndex === index}
                    onToggle={() => setOpenSectionIndex(openSectionIndex === index ? -1 : index)}
                  />
                ))}
                <button type="button" className={styles.addSectionInline} onClick={addSection}>
                  <span>+</span>
                  Thêm mục
                </button>
              </div>
            </div>
          </div>

          <aside className={`${styles.outlineCard} ${styles.previewAside}`}>
            <div>
              <h2 className={styles.sectionTitle}>Xem trước dàn ý</h2>
              <p className={styles.sectionHint}>Bấm từng mục để xem chi tiết</p>
            </div>
            <OutlinePreview sections={sections} sampleTitle={titleTags[0]} />
          </aside>
        </div>

        {loading && (
          <div className={`${styles.bannerLoading} ${styles.geminiResponseLoading}`}>
            <span className={styles.geminiPulse} aria-hidden="true" />
            <strong>AI đang dựng bản nháp</strong>
            <em>Đang lập dàn ý, viết từng phần và gom kết quả về giao diện...</em>
          </div>
        )}
        {error && <div className={styles.bannerError}>{error}</div>}
        <div className={styles.sectionActions}>
          <div className={styles.creditEstimateCard}>
            <span>Credit hiện có: {Number(estimate?.credit_balance ?? activeSubscription?.credit_balance ?? user?.credit_balance ?? 0).toFixed(6)}</span>
            <strong>
              {estimating
                ? "Đang dự đoán..."
                : estimate
                  ? `Dự đoán tốn ~${Number(estimate.credit_cost || 0).toFixed(6)} credit`
                  : "Nhập đủ thông tin để dự đoán credit"}
            </strong>
            <em>Chỉ là ước tính tương đối, chi phí thực tế sẽ tính theo token input/output sau khi gen.</em>
          </div>
          <button type="button" className={styles.buttonPrimary} onClick={submit} disabled={loading}>
            {loading ? "Đang tạo..." : "Tạo bài viết"}
          </button>
          <button
            type="button"
            className={styles.buttonGhost}
            onClick={() => {
              resetBuilder();
              setTitleDraft("");
              setStyleDraft("");
              setShowStyleSuggestions(false);
              setStyleSuggestions([]);
              setOutlineLayouts([]);
              setOutlineDescription("");
              setOpenSectionIndex(-1);
              setPosts([]);
              setEstimate(null);
              setError(null);
            }}
            disabled={loading}
          >
            Đặt lại
          </button>
        </div>
      </section>

      <OutlineSuggestionModal
        open={outlineModalOpen}
        description={outlineDescription}
        layouts={outlineLayouts}
        loading={suggestingOutlines}
        onDescriptionChange={setOutlineDescription}
        onGenerate={() => loadOutlineSuggestions()}
        onSelect={selectOutlineLayout}
        onClose={() => setOutlineModalOpen(false)}
      />

      {posts.length > 0 && <ResultsPanel posts={posts} />}
    </div>
  );
}

export default PostFormModern;
