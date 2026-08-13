import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import {
  defaultResumeInput,
  hasResumeInput,
  ResumeInput,
} from "../../src/components/ResumeInput";

describe("hasResumeInput", () => {
  it("is false for empty or whitespace-only text", () => {
    expect(hasResumeInput(defaultResumeInput)).toBe(false);
    expect(
      hasResumeInput({ ...defaultResumeInput, resume: "   \n  " })
    ).toBe(false);
  });

  it("is true when text or a PDF file is present", () => {
    expect(
      hasResumeInput({ ...defaultResumeInput, resume: "Experience..." })
    ).toBe(true);
    expect(
      hasResumeInput({
        ...defaultResumeInput,
        pdfFile: new File(["pdf"], "resume.pdf", { type: "application/pdf" }),
      })
    ).toBe(true);
  });
});

describe("ResumeInput", () => {
  it("matches markup snapshot", () => {
    const { container } = render(
      <ResumeInput
        value={defaultResumeInput}
        onChange={() => {}}
        onError={() => {}}
      />
    );
    expect(container.querySelector("section")).toMatchSnapshot();
  });

  it("shows an error for unsupported file types", () => {
    const onError = vi.fn();
    const onChange = vi.fn();

    render(
      <ResumeInput
        value={defaultResumeInput}
        onChange={onChange}
        onError={onError}
      />
    );

    const input = document.getElementById("resume-file") as HTMLInputElement;
    const file = new File(["doc"], "resume.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    fireEvent.change(input, { target: { files: [file] } });

    expect(onError).toHaveBeenCalledWith(
      "Please choose a .txt, .md, or .pdf resume file."
    );
    expect(onChange).not.toHaveBeenCalled();
  });

  it("loads text file contents into resume state", async () => {
    const onError = vi.fn();
    const onChange = vi.fn();
    const textSpy = vi
      .spyOn(File.prototype, "text")
      .mockResolvedValue("Alex Morgan\nEngineer");

    render(
      <ResumeInput
        value={defaultResumeInput}
        onChange={onChange}
        onError={onError}
      />
    );

    const input = document.getElementById("resume-file") as HTMLInputElement;
    const file = new File(["Alex Morgan\nEngineer"], "resume.txt", {
      type: "text/plain",
    });
    fireEvent.change(input, { target: { files: [file] } });

    await vi.waitFor(() => {
      expect(onChange).toHaveBeenCalledWith({
        resume: "Alex Morgan\nEngineer",
        pdfFile: null,
        fileName: "resume.txt",
      });
    });
    expect(onError).toHaveBeenCalledWith(null);
    textSpy.mockRestore();
  });

  it("shows PDF notice when a PDF is attached", () => {
    render(
      <ResumeInput
        value={{
          resume: "",
          pdfFile: new File(["pdf"], "resume.pdf", { type: "application/pdf" }),
          fileName: "resume.pdf",
        }}
        onChange={() => {}}
        onError={() => {}}
      />
    );

    expect(screen.getByText("resume.pdf")).toBeInTheDocument();
    expect(
      screen.getByText(/PDF resume attached\. Text will be extracted on the server/)
    ).toBeInTheDocument();
  });

  it("reveals paste textarea when Paste resume is clicked", async () => {
    const user = userEvent.setup();

    render(
      <ResumeInput
        value={defaultResumeInput}
        onChange={() => {}}
        onError={() => {}}
      />
    );

    await user.click(screen.getByRole("button", { name: "Paste resume" }));

    expect(screen.getByPlaceholderText("Paste resume text...")).toBeInTheDocument();
  });
});
