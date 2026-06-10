import { useMemo, useState } from "react";

const createSection = () => ({
  title: "",
  role: "",
  word_count: 250,
  description: "",
});

// Normalize Unicode string to NFC (composed form) to fix Vietnamese character issues
const normalizeString = (str) => {
  if (typeof str !== "string") return str;
  return str.normalize("NFC");
};

function usePostComposer() {
  const [titles, setTitles] = useState("");
  const [style, setStyle] = useState("");
  const [sections, setSections] = useState([createSection()]);
  const [submitted, setSubmitted] = useState(false);

  // Wrapper functions to normalize input immediately
  const handleSetTitles = (value) => {
    setTitles(normalizeString(value));
  };

  const handleSetStyle = (value) => {
    setStyle(normalizeString(value));
  };

  const normalizedTitles = useMemo(
    () =>
      normalizeString(titles)
        .split(/\r?\n/)
        .map((line) => normalizeString(line.trim()))
        .filter(Boolean),
    [titles],
  );

  const totalTargetWords = useMemo(
    () =>
      sections.reduce((sum, section) => {
        const parsed = Number(section.word_count);
        return sum + (Number.isFinite(parsed) ? parsed : 0);
      }, 0),
    [sections],
  );

  const payload = useMemo(
    () => ({
      titles: normalizedTitles,
      style: normalizeString(style.trim()),
      sections: sections.map((section) => ({
        title: normalizeString(section.title.trim()),
        role: normalizeString(section.role.trim()),
        word_count: Number(section.word_count),
        description: normalizeString(section.description.trim()),
      })),
    }),
    [normalizedTitles, sections, style],
  );

  const addSection = () => {
    setSections((current) => [...current, createSection()]);
  };

  const removeSection = (index) => {
    setSections((current) => (current.length === 1 ? current : current.filter((_, currentIndex) => currentIndex !== index)));
  };

  const updateSection = (index, field, value) => {
    setSections((current) =>
      current.map((section, currentIndex) =>
        currentIndex === index
          ? {
              ...section,
              [field]: field === "word_count" ? value.replace(/[^\d]/g, "") : normalizeString(value),
            }
          : section,
      ),
    );
  };

  const replaceSections = (nextSections) => {
    const cleanedSections = nextSections
      .map((section) => ({
        title: normalizeString(section.title || ""),
        role: normalizeString(section.role || ""),
        word_count: String(section.word_count || 250).replace(/[^\d]/g, "") || "250",
        description: normalizeString(section.description || ""),
      }))
      .filter((section) => section.title || section.role || section.description);
    setSections(cleanedSections.length ? cleanedSections : [createSection()]);
  };

  const validate = (candidatePayload = payload) => {
    if (!candidatePayload.titles.length || !candidatePayload.style) {
      return false;
    }

    return candidatePayload.sections.every(
      (section) =>
        section.title &&
        section.role &&
        section.description &&
        Number.isFinite(section.word_count) &&
        section.word_count >= 50,
    );
  };

  const handleSubmit = (overrides = {}) => {
    setSubmitted(true);
    const candidatePayload = {
      ...payload,
      ...overrides,
      style: normalizeString((overrides.style ?? payload.style).trim()),
    };
    return validate(candidatePayload) ? candidatePayload : null;
  };

  const resetBuilder = () => {
    handleSetTitles("");
    handleSetStyle("");
    setSections([createSection()]);
    setSubmitted(false);
  };

  return {
    titles,
    setTitles: handleSetTitles,
    style,
    setStyle: handleSetStyle,
    sections,
    submitted,
    normalizedTitles,
    totalTargetWords,
    addSection,
    removeSection,
    updateSection,
    replaceSections,
    handleSubmit,
    resetBuilder,
  };
}

export default usePostComposer;
