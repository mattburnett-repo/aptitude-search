import { useState } from "react";

type SaveAsPdfToolbarProps = {
  contentRef: React.RefObject<HTMLDivElement | null>;
  loadExporter: () => Promise<(element: HTMLElement) => Promise<void>>;
};

export function SaveAsPdfToolbar({ contentRef, loadExporter }: SaveAsPdfToolbarProps) {
  const [pdfBusy, setPdfBusy] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);

  async function handleSaveAsPdf() {
    const element = contentRef.current;
    if (!element || pdfBusy) return;

    setPdfError(null);
    setPdfBusy(true);
    try {
      const openPdf = await loadExporter();
      await openPdf(element);
    } catch (err) {
      setPdfError(
        err instanceof Error ? err.message : "Could not create PDF. Try again."
      );
    } finally {
      setPdfBusy(false);
    }
  }

  return (
    <div className="pdf-export-actions">
      <button
        type="button"
        className="secondary"
        disabled={pdfBusy}
        onClick={() => void handleSaveAsPdf()}
      >
        {pdfBusy ? "Generating PDF…" : "Save as PDF"}
      </button>
      {pdfError && <p className="error pdf-export-error">{pdfError}</p>}
    </div>
  );
}
