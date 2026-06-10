export function sanitizeVietnameseText(input) {
  let text = input == null ? "" : String(input);

  // Fix common Mojibake/control-char artifacts that show up in PDF text extraction/rendering.
  // - Replace any C0 control chars except \n\r\t
  // - Remove ISO-8859/Windows-1252 style replacement markers that may appear as \uFFFD
  // - Normalize weird whitespace
  text = text.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, " ");
  text = text.replace(/\uFFFD/g, " ");

  // Collapse whitespace but keep new lines
  text = text
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .replace(/[\t ]+/g, " ");

  return text.trim();
}

