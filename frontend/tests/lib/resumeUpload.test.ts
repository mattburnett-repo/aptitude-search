import { describe, expect, it } from "vitest";
import {
  isPdfResumeFile,
  isSupportedResumeFile,
  isTextResumeFile,
} from "../../src/lib/resumeUpload";

function file(name: string, type = ""): File {
  return new File(["content"], name, { type });
}

describe("resumeUpload", () => {
  describe("isPdfResumeFile", () => {
    it("accepts .pdf extension", () => {
      expect(isPdfResumeFile(file("resume.pdf"))).toBe(true);
    });

    it("accepts application/pdf MIME type", () => {
      expect(isPdfResumeFile(file("resume", "application/pdf"))).toBe(true);
    });

    it("rejects text files", () => {
      expect(isPdfResumeFile(file("resume.txt", "text/plain"))).toBe(false);
    });
  });

  describe("isTextResumeFile", () => {
    it("accepts .txt and .md extensions", () => {
      expect(isTextResumeFile(file("resume.txt"))).toBe(true);
      expect(isTextResumeFile(file("resume.md"))).toBe(true);
    });

    it("accepts text/* MIME types", () => {
      expect(isTextResumeFile(file("resume", "text/plain"))).toBe(true);
    });

    it("rejects PDF files", () => {
      expect(isTextResumeFile(file("resume.pdf", "application/pdf"))).toBe(
        false
      );
    });
  });

  describe("isSupportedResumeFile", () => {
    it("accepts PDF and text resume types", () => {
      expect(isSupportedResumeFile(file("resume.pdf"))).toBe(true);
      expect(isSupportedResumeFile(file("resume.txt"))).toBe(true);
    });

    it("rejects unsupported extensions", () => {
      expect(isSupportedResumeFile(file("resume.docx"))).toBe(false);
    });
  });
});
