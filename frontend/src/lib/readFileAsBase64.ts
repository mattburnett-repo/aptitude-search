// Encode a PDF File as base64 for JSON upload. Text extraction happens on the backend.
function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result !== "string") {
        reject(new Error("Could not read PDF file."));
        return;
      }
      const base64 = reader.result.split(",", 2)[1];
      if (!base64) {
        reject(new Error("Could not read PDF file."));
        return;
      }
      resolve(base64);
    };
    reader.onerror = () => reject(new Error("Could not read PDF file."));
    reader.readAsDataURL(file);
  });
}

export { readFileAsBase64 };
