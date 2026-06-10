import JSZip from "jszip";
import { downloadHtmlAsPdf } from "./downloadHtmlAsPdf";
import { addCanvasToPdfPages } from "./htmlToPdf";

export async function exportSingleHistoryItemToPdf({ item }) {
  return downloadHtmlAsPdf({
    title: item?.title ? `Bai: ${item.title}` : `Bai ${item?.id ?? ""}`,
    html: item?.content || "",
    fileNamePrefix: "history",
  });
}

export async function exportHistoryByPostIdToPdf({ items, postId }) {
  const safePostId = postId ?? "";
  const combinedHtml = (items || []).map((it) => `<article>${it?.content || ""}</article>`).join("\n");

  return downloadHtmlAsPdf({
    title: `Post ${safePostId}`,
    html: combinedHtml,
    fileNamePrefix: `history-post-${safePostId}`,
  });
}

/**
 * Export multiple history items as separate PDFs in a ZIP archive.
 */
export async function exportMultipleHistoriesToZip(items) {
  if (!items || items.length === 0) return;

  const zip = new JSZip();

  for (const item of items) {
    const pdfPromise = await generateHistoryItemPdf(item);
    const fileName = generateFileName(item);
    zip.file(`${fileName}.pdf`, pdfPromise, { binary: true });
  }

  const zipBlob = await zip.generateAsync({ type: "blob" });
  const url = URL.createObjectURL(zipBlob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `history-batch-${new Date().getTime()}.zip`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

async function generateHistoryItemPdf(item) {
  const jsPDF = await import("jspdf").then((m) => m.default);
  const html2canvas = await import("html2canvas").then((m) => m.default);

  const pdf = new jsPDF({
    orientation: "p",
    unit: "pt",
    format: "a4",
  });

  const pageWidth = 595.28;
  const pageHeight = 841.89;

  const container = document.createElement("div");
  container.style.position = "fixed";
  container.style.left = "-10000px";
  container.style.top = "0";
  container.style.width = `${pageWidth - 56}px`;
  container.style.background = "white";
  container.style.padding = "0";
  container.style.boxSizing = "border-box";
  container.style.color = "#111827";
  container.style.fontFamily = "Arial, sans-serif";
  container.style.fontSize = "14px";
  container.style.lineHeight = "1.65";

  const contentEl = document.createElement("div");
  contentEl.innerHTML = item?.content || "";

  container.appendChild(contentEl);
  document.body.appendChild(container);

  try {
    const canvas = await html2canvas(container, {
      scale: 2,
      useCORS: true,
      backgroundColor: "#ffffff",
      logging: false,
      windowWidth: container.scrollWidth,
    });

    addCanvasToPdfPages(pdf, canvas, pageWidth, pageHeight);

    return pdf.output("arraybuffer");
  } finally {
    document.body.removeChild(container);
  }
}

function generateFileName(item) {
  const timestamp = item?.changed_at ? new Date(item.changed_at).getTime() : Date.now();
  const title = item?.title || "bai";
  const safeName = title
    .replaceAll(/[^a-zA-Z0-9\-_ ]/g, "")
    .trim()
    .replaceAll(/\s+/g, "-")
    .toLowerCase()
    .substring(0, 50);
  return `${safeName}-${timestamp}`;
}
