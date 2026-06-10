// Helper for embedding a Unicode font into jsPDF.
// NOTE: You must provide the actual .ttf file(s) in your project.
// Place a Vietnamese-capable font file (e.g. NotoSans-Regular.ttf) under:
//   fe_react_UI/src/assets/fonts/NotoSans-Regular.ttf
// Then update FONT_PATH accordingly.

import TimesFontUrl from "@/assets/fonts/times.ttf?url";

export const FONT_NAME = "Times";
export const FONT_PATH_URL = TimesFontUrl;


export async function registerFontForJsPdf(doc) {
  // jsPDF v2+ expects font in base64 (or VFS) depending on method.
  // We convert the URL to base64 at runtime.
  const res = await fetch(FONT_PATH_URL);
  const blob = await res.blob();

  const base64 = await blobToBase64(blob);

  // Format: base64 string without data prefix
  const fontBase64 = base64;

  // Add font to VFS and register.
  // Some builds support addFileToVFS/addFont; if not, adjust to your jsPDF version.
  doc.addFileToVFS(`${FONT_NAME}.ttf`, fontBase64);
  doc.addFont(`${FONT_NAME}.ttf`, FONT_NAME, "normal");

  // Set as default
  doc.setFont(FONT_NAME);
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const dataUrl = String(reader.result || "");
      // data:font/ttf;base64,xxxx
      const parts = dataUrl.split(",");
      resolve(parts.length > 1 ? parts[1] : "");
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

