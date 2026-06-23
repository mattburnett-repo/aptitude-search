import type { jsPDF } from "jspdf";

// html2canvas and jspdf are loaded via import() below so Vite emits separate
// chunks; they download only on the first Save as PDF, not on initial page load.

const PDF_MARGIN_PT = 36;

type PdfLibs = {
  html2canvas: (typeof import("html2canvas"))["default"];
  jsPDF: typeof import("jspdf").jsPDF;
};

let pdfLibsPromise: Promise<PdfLibs> | null = null;

function loadPdfLibs(): Promise<PdfLibs> {
  if (!pdfLibsPromise) {
    pdfLibsPromise = Promise.all([import("html2canvas"), import("jspdf")]).then(
      ([html2canvasModule, jspdfModule]) => ({
        html2canvas: html2canvasModule.default,
        jsPDF: jspdfModule.jsPDF,
      })
    );
  }
  return pdfLibsPromise;
}

function prepareCloneForExport(doc: Document, clone: HTMLElement) {
  clone.classList.add("aptitude-profile", "aptitude-profile--pdf-export");
  flattenInferenceConfidenceForExport(doc, clone);
  for (const node of clone.querySelectorAll("details")) {
    if (node instanceof HTMLDetailsElement) {
      node.open = true;
    }
  }
}

function flattenInferenceConfidenceForExport(doc: Document, root: HTMLElement) {
  for (const details of root.querySelectorAll(".aptitude-meta")) {
    if (!(details instanceof HTMLDetailsElement)) continue;

    const summary = details.querySelector("summary");
    const body = details.querySelector(".collapsible-section-body");
    if (!summary || !body) continue;

    const section = doc.createElement("section");
    section.className = "aptitude-section aptitude-inference-confidence-pdf";

    const heading = doc.createElement("h3");
    heading.className = "aptitude-section-title";
    heading.textContent = summary.textContent?.trim() ?? "Inference confidence";
    section.appendChild(heading);

    while (body.firstChild) {
      section.appendChild(body.firstChild);
    }

    details.replaceWith(section);
  }
}

function isPdfPageEmpty(element: HTMLElement): boolean {
  return !element.textContent?.trim();
}

async function capturePageElement(
  html2canvas: PdfLibs["html2canvas"],
  element: HTMLElement
): Promise<HTMLCanvasElement> {
  return html2canvas(element, {
    scale: 2,
    useCORS: true,
    backgroundColor: "#ffffff",
    onclone: (doc, clone) => {
      prepareCloneForExport(doc, clone);
    },
  });
}

function appendCanvasToPdf(
  pdf: jsPDF,
  canvas: HTMLCanvasElement,
  options: { newPageBefore: boolean; isFirstContent: boolean }
) {
  const imgData = canvas.toDataURL("image/png");
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const contentWidth = pageWidth - PDF_MARGIN_PT * 2;
  const printableHeight = pageHeight - PDF_MARGIN_PT * 2;
  const imgWidth = contentWidth;
  const imgHeight = (canvas.height * imgWidth) / canvas.width;

  let heightLeft = imgHeight;
  let position = 0;
  let slice = 0;

  while (heightLeft > 0) {
    const isContinuation = slice > 0;
    const shouldAddPage =
      isContinuation ||
      (options.newPageBefore && !options.isFirstContent && slice === 0);

    if (shouldAddPage) {
      pdf.addPage();
    }

    pdf.addImage(
      imgData,
      "PNG",
      PDF_MARGIN_PT,
      PDF_MARGIN_PT + position,
      imgWidth,
      imgHeight
    );

    heightLeft -= printableHeight;
    position = heightLeft - imgHeight;
    slice += 1;
  }
}

export async function openAptitudeProfilePdf(element: HTMLElement): Promise<void> {
  const { html2canvas, jsPDF: JsPDF } = await loadPdfLibs();
  const pageElements = Array.from(
    element.querySelectorAll<HTMLElement>("[data-pdf-page]")
  ).filter((page) => !isPdfPageEmpty(page));

  const pdf = new JsPDF({ orientation: "p", unit: "pt", format: "a4" });
  let isFirstContent = true;

  if (pageElements.length === 0) {
    const canvas = await capturePageElement(html2canvas, element);
    appendCanvasToPdf(pdf, canvas, {
      newPageBefore: false,
      isFirstContent: true,
    });
  } else {
    for (const pageElement of pageElements) {
      const canvas = await capturePageElement(html2canvas, pageElement);
      appendCanvasToPdf(pdf, canvas, {
        newPageBefore: true,
        isFirstContent,
      });
      isFirstContent = false;
    }
  }

  const blob = pdf.output("blob");
  const url = URL.createObjectURL(blob);
  const tab = window.open(url, "_blank", "noopener,noreferrer");

  // noopener returns null in modern browsers even when the tab opens.
  if (tab) {
    tab.addEventListener("load", () => URL.revokeObjectURL(url), { once: true });
    return;
  }

  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
