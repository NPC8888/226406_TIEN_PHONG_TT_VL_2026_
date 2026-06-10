import jsPDF from "jspdf";
import html2canvas from "html2canvas";

function toA4PtDimensions() {
  // jsPDF uses pt when unit=pt. a4 = 595.28 x 841.89 pt
  return {
    width: 595.28,
    height: 841.89,
  };
}

function escapeFilePart(str) {
  return String(str ?? "")
    .replaceAll(/[^a-zA-Z0-9\-_ ]/g, "")
    .trim()
    .replaceAll(/\s+/g, "-")
    .toLowerCase();
}

function getRowInkScore(data, width, y) {
  const step = 5;
  let inkPixels = 0;
  let sampledPixels = 0;
  for (let x = 0; x < width; x += step) {
    const offset = (y * width + x) * 4;
    sampledPixels += 1;
    if (data[offset + 3] > 12 && (data[offset] < 245 || data[offset + 1] < 245 || data[offset + 2] < 245)) {
      inkPixels += 1;
    }
  }
  return sampledPixels ? inkPixels / sampledPixels : 0;
}

function findPageBreak(data, width, startY, targetY, minY, maxY) {
  const quietThreshold = 0.0035;
  const requiredQuietRows = 14;
  const safeMinY = Math.max(startY + 80, minY);
  const safeMaxY = Math.min(targetY - 8, maxY);
  let bestY = safeMaxY;
  let bestScore = Number.POSITIVE_INFINITY;

  for (let y = safeMaxY; y >= safeMinY; y -= 1) {
    let quietRows = 0;
    let score = 0;
    for (let row = y; row > Math.max(startY, y - requiredQuietRows); row -= 1) {
      const rowScore = getRowInkScore(data, width, row);
      score += rowScore;
      if (rowScore <= quietThreshold) quietRows += 1;
    }

    if (quietRows >= requiredQuietRows) {
      return y - Math.floor(requiredQuietRows / 2);
    }

    const averageScore = score / requiredQuietRows;
    if (averageScore < bestScore) {
      bestScore = averageScore;
      bestY = y - Math.floor(requiredQuietRows / 2);
    }
  }

  return bestY;
}

export function addCanvasToPdfPages(pdf, canvas, pageWidth, pageHeight) {
  const pageMarginPt = 28;
  const printableWidthPt = pageWidth - pageMarginPt * 2;
  const printableHeightPt = pageHeight - pageMarginPt * 2;
  const pageHeightPx = Math.floor((printableHeightPt * canvas.width) / printableWidthPt);
  const imageData = canvas.getContext("2d").getImageData(0, 0, canvas.width, canvas.height);
  const sliceCanvas = document.createElement("canvas");
  const sliceContext = sliceCanvas.getContext("2d");
  let sourceY = 0;

  while (sourceY < canvas.height) {
    const remainingPx = canvas.height - sourceY;
    let sliceHeightPx = Math.min(pageHeightPx, remainingPx);

    if (remainingPx > pageHeightPx) {
      const targetY = sourceY + pageHeightPx;
      const minY = sourceY + Math.floor(pageHeightPx * 0.62);
      const maxY = sourceY + pageHeightPx - 18;
      sliceHeightPx = findPageBreak(
        imageData.data,
        canvas.width,
        sourceY,
        targetY,
        minY,
        maxY
      ) - sourceY;
    }

    sliceCanvas.width = canvas.width;
    sliceCanvas.height = sliceHeightPx;
    sliceContext.fillStyle = "#ffffff";
    sliceContext.fillRect(0, 0, sliceCanvas.width, sliceCanvas.height);
    sliceContext.drawImage(
      canvas,
      0,
      sourceY,
      canvas.width,
      sliceHeightPx,
      0,
      0,
      canvas.width,
      sliceHeightPx
    );

    const imgData = sliceCanvas.toDataURL("image/png");
    const sliceHeightPt = (sliceHeightPx * printableWidthPt) / canvas.width;
    pdf.addImage(imgData, "PNG", pageMarginPt, pageMarginPt, printableWidthPt, sliceHeightPt);

    sourceY += sliceHeightPx;
    if (sourceY < canvas.height) {
      pdf.addPage();
    }
  }
}

export async function downloadHtmlToPdf({
  title = "export",
  html = "",
  fileNamePrefix = "history",
  scale = 2,
  includeTitle = false,
} = {}) {
  const pdf = new jsPDF({
    orientation: "p",
    unit: "pt",
    format: "a4",
  });

  const { width: pageWidth, height: pageHeight } = toA4PtDimensions();

  // Create an offscreen container to render the HTML with browser text/layout engine
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
  contentEl.innerHTML = html || "";

  if (includeTitle) {
    const titleEl = document.createElement("div");
    titleEl.style.fontWeight = "700";
    titleEl.style.fontSize = "18px";
    titleEl.style.marginBottom = "12px";
    titleEl.textContent = title;
    container.appendChild(titleEl);
  }
  container.appendChild(contentEl);
  document.body.appendChild(container);

  try {
    const canvas = await html2canvas(container, {
      scale,
      useCORS: true,
      backgroundColor: "#ffffff",
      logging: false,
      // Let browser compute layout height based on content
      windowWidth: container.scrollWidth,
    });

    addCanvasToPdfPages(pdf, canvas, pageWidth, pageHeight);

    const safeTitle = escapeFilePart(title);
    pdf.save(`${fileNamePrefix}-${safeTitle}.pdf`);
  } finally {
    document.body.removeChild(container);
  }
}

