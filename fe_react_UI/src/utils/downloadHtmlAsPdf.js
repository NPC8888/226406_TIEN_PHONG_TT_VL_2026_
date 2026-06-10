import { downloadHtmlToPdf } from "./htmlToPdf";

export async function downloadHtmlAsPdf({
  title = "export",
  html = "",
  fileNamePrefix = "history",
} = {}) {
  return downloadHtmlToPdf({ title, html, fileNamePrefix });
}

