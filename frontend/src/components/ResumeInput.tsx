import { useRef, useState } from "react";
import {
  isPdfResumeFile,
  isSupportedResumeFile,
  isTextResumeFile,
} from "../lib/resumeUpload";

export type ResumeInputValue = {
  resume: string;
  pdfFile: File | null;
  fileName: string | null;
};

export const defaultResumeInput: ResumeInputValue = {
  resume: "",
  pdfFile: null,
  fileName: null,
};

export function hasResumeInput(value: ResumeInputValue) {
  return Boolean(value.resume.trim() || value.pdfFile);
}

type ResumeInputProps = {
  value: ResumeInputValue;
  onChange: (value: ResumeInputValue) => void;
  onError: (message: string | null) => void;
};

export function ResumeInput({ value, onChange, onError }: ResumeInputProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [showPasteInput, setShowPasteInput] = useState(false);

  const showTextarea =
    showPasteInput || Boolean(value.fileName && value.resume && !value.pdfFile);

  const inPasteMode = showPasteInput && !value.pdfFile && !value.fileName;

  async function handleFileSelect(file: File) {
    if (!isSupportedResumeFile(file)) {
      onError("Please choose a .txt, .md, or .pdf resume file.");
      return;
    }

    if (isPdfResumeFile(file)) {
      setShowPasteInput(false);
      onChange({ resume: "", pdfFile: file, fileName: file.name });
      onError(null);
      return;
    }

    if (!isTextResumeFile(file)) {
      onError("Please choose a .txt, .md, or .pdf resume file.");
      return;
    }

    try {
      const text = await file.text();
      setShowPasteInput(false);
      onChange({ resume: text, pdfFile: null, fileName: file.name });
      onError(null);
    } catch {
      onError("Could not read the selected file.");
    }
  }

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) void handleFileSelect(file);
    event.target.value = "";
  }

  function handleTextChange(event: React.ChangeEvent<HTMLTextAreaElement>) {
    onChange({
      resume: event.target.value,
      pdfFile: null,
      fileName: null,
    });
  }

  function clearFile() {
    setShowPasteInput(false);
    onChange(defaultResumeInput);
  }

  function openPasteInput() {
    setShowPasteInput(true);
    requestAnimationFrame(() => textareaRef.current?.focus());
  }

  function closePasteInput() {
    setShowPasteInput(false);
    onChange({ resume: "", pdfFile: null, fileName: null });
  }

  return (
    <section>
      <div className="resume-toolbar">
        <input
          ref={fileInputRef}
          id="resume-file"
          type="file"
          accept=".txt,.md,.text,.pdf,text/plain,application/pdf"
          className="resume-file-input"
          onChange={handleFileChange}
          aria-label="Resume file"
        />
        <button
          type="button"
          className="secondary resume-file-button"
          onClick={() => fileInputRef.current?.click()}
        >
          Choose resume file
        </button>
        {value.fileName && (
          <span className="resume-file-name">{value.fileName}</span>
        )}
        {value.pdfFile && (
          <button
            type="button"
            className="secondary resume-file-button"
            onClick={clearFile}
          >
            Clear file
          </button>
        )}
        {!showTextarea && !value.pdfFile && (
          <button
            type="button"
            className="secondary resume-file-button"
            onClick={openPasteInput}
          >
            Paste resume
          </button>
        )}
        {inPasteMode && (
          <button
            type="button"
            className="secondary resume-file-button"
            onClick={closePasteInput}
          >
            Hide paste
          </button>
        )}
      </div>
      {value.pdfFile && (
        <p className="resume-pdf-notice">
          PDF resume attached. Text will be extracted on the server when you run
          the pipeline.
        </p>
      )}
      {showTextarea && (
        <textarea
          ref={textareaRef}
          id="resume"
          value={value.resume}
          onChange={handleTextChange}
          placeholder="Paste resume text..."
          aria-label="Resume text"
        />
      )}
    </section>
  );
}
