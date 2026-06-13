const TEXT_EXTENSIONS = new Set(["txt", "md", "text", "markdown"]);

// PDF resumes are sent as base64 JSON; text files are read in the browser.
export function isPdfResumeFile(file: File): boolean {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  return extension === "pdf" || file.type === "application/pdf";
}

export function isTextResumeFile(file: File): boolean {
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  return TEXT_EXTENSIONS.has(extension) || file.type.startsWith("text/");
}

export function isSupportedResumeFile(file: File): boolean {
  return isPdfResumeFile(file) || isTextResumeFile(file);
}
