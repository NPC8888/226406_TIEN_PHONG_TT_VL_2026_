import { useMemo, useState } from "react";

const toRoman = (num) => {
  const roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"];
  return roman[num - 1] || num;
};

// Normalize Unicode string to NFC (composed form) to fix Vietnamese character issues
const normalizeString = (str) => {
  if (typeof str !== "string") return str;
  return str.normalize("NFC");
};

const usePostBuilder = () => {
  const [titles, setTitles] = useState("");
  const [style, setStyle] = useState("");
  const [sections, setSections] = useState([{ title: "", desc: "" }]);
  const [submitted, setSubmitted] = useState(false);

  // Wrapper functions to normalize input immediately
  const handleSetTitles = (value) => {
    setTitles(normalizeString(value));
  };

  const handleSetStyle = (value) => {
    setStyle(normalizeString(value));
  };

  const payload = useMemo(() => {
    const cleanedTitles = normalizeString(titles)
      .split(/\r?\n/)
      .map((line) => normalizeString(line.trim()))
      .filter((line) => line !== "");

    return {
      titles: cleanedTitles,
      style: normalizeString(style.trim()),
      sections: sections.map((sec) => ({
        title: normalizeString(sec.title),
        desc: normalizeString(sec.desc),
      })),
    };
  }, [titles, style, sections]);

  const addSection = () => {
    setSections((prev) => [...prev, { title: "", desc: "" }]);
  };

  const removeSection = (index) => {
    setSections((prev) => prev.filter((_, i) => i !== index));
  };

  const updateSection = (index, field, value) => {
    setSections((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: normalizeString(value) };
      return next;
    });
  };

  const validate = () => {
    if (!payload.titles.length) {
      return false;
    }
    if (payload.sections.some((sec) => !sec.title.trim())) {
      return false;
    }
    return true;
  };

  const handleSubmit = () => {
    setSubmitted(true);
    if (!validate()) {
      return null;
    }
    console.log("Payload sent to backend:", payload);
    return payload;
  };

  const resetBuilder = () => {
    handleSetTitles("");
    handleSetStyle("");
    setSections([{ title: "", desc: "" }]);
    setSubmitted(false);
  };

  return {
    titles,
    setTitles: handleSetTitles,
    style,
    setStyle: handleSetStyle,
    sections,
    payload,
    submitted,
    addSection,
    removeSection,
    updateSection,
    handleSubmit,
    resetBuilder,
    toRoman,
  };
};

export default usePostBuilder;
