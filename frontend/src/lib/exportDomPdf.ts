import type { jsPDF } from "jspdf";

// html2canvas and jspdf load via import() so Vite emits separate chunks.

export const PDF_MARGIN_PT = 36;

export type PdfLibs = {
  html2canvas: (typeof import("html2canvas"))["default"];
  jsPDF: typeof import("jspdf").jsPDF;
};

export type PrepareCloneFn = (doc: Document, clone: HTMLElement) => void;

export type PdfLinkAnnotation = {
  url: string;
  x: number;
  y: number;
  width: number;
  height: number;
};

export type CaptureResult = {
  canvas: HTMLCanvasElement;
  links: PdfLinkAnnotation[];
  sourceWidth: number;
  sourceHeight: number;
};

let pdfLibsPromise: Promise<PdfLibs> | null = null;

export function loadPdfLibs(): Promise<PdfLibs> {
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

export function isPdfPageEmpty(element: HTMLElement): boolean {
  return !element.textContent?.trim();
}

function collectPdfLinks(root: HTMLElement): PdfLinkAnnotation[] {
  const rootRect = root.getBoundingClientRect();
  const links: PdfLinkAnnotation[] = [];

  for (const node of root.querySelectorAll<HTMLAnchorElement>("a[href]")) {
    const url = node.href;
    if (!url) continue;

    const rect = node.getBoundingClientRect();
    links.push({
      url,
      x: rect.left - rootRect.left,
      y: rect.top - rootRect.top,
      width: rect.width,
      height: rect.height,
    });
  }

  return links;
}

export async function captureElement(
  html2canvas: PdfLibs["html2canvas"],
  element: HTMLElement,
  prepareClone: PrepareCloneFn
): Promise<CaptureResult> {
  let links: PdfLinkAnnotation[] = [];
  let sourceWidth = element.offsetWidth;
  let sourceHeight = element.offsetHeight;

  const canvas = await html2canvas(element, {
    scale: 2,
    useCORS: true,
    backgroundColor: "#ffffff",
    onclone: (_doc, clone) => {
      prepareClone(_doc, clone);
      links = collectPdfLinks(clone);
      sourceWidth = clone.offsetWidth;
      sourceHeight = clone.offsetHeight;
    },
  });

  return { canvas, links, sourceWidth, sourceHeight };
}

export function appendCanvasToPdf(
  pdf: jsPDF,
  capture: CaptureResult,
  options: { newPageBefore: boolean; isFirstContent: boolean }
) {
  const { canvas, links, sourceWidth, sourceHeight } = capture;
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

    if (sourceWidth > 0 && sourceHeight > 0) {
      const sliceTop = PDF_MARGIN_PT;
      const sliceBottom = PDF_MARGIN_PT + printableHeight;

      for (const link of links) {
        const pdfLinkX = PDF_MARGIN_PT + (link.x / sourceWidth) * imgWidth;
        const pdfLinkY =
          PDF_MARGIN_PT + position + (link.y / sourceHeight) * imgHeight;
        const pdfLinkW = (link.width / sourceWidth) * imgWidth;
        const pdfLinkH = (link.height / sourceHeight) * imgHeight;

        if (pdfLinkY + pdfLinkH > sliceTop && pdfLinkY < sliceBottom) {
          pdf.link(pdfLinkX, pdfLinkY, pdfLinkW, pdfLinkH, { url: link.url });
        }
      }
    }

    heightLeft -= printableHeight;
    position = heightLeft - imgHeight;
    slice += 1;
  }
}

export function maxSourceHeightPx(sourceWidthPx: number): number {
  const pageWidth = 595.28;
  const pageHeight = 841.89;
  const contentWidth = pageWidth - PDF_MARGIN_PT * 2;
  const printableHeight = pageHeight - PDF_MARGIN_PT * 2;
  return (printableHeight * sourceWidthPx) / contentWidth;
}

export async function openPackedDomPdf(
  pages: HTMLElement[],
  prepareClone: PrepareCloneFn
): Promise<void> {
  const { html2canvas, jsPDF: JsPDF } = await loadPdfLibs();
  const pdf = new JsPDF({ orientation: "p", unit: "pt", format: "a4" });
  let isFirstContent = true;

  for (const pageElement of pages.filter((page) => !isPdfPageEmpty(page))) {
    const capture = await captureElement(html2canvas, pageElement, prepareClone);
    appendCanvasToPdf(pdf, capture, {
      newPageBefore: true,
      isFirstContent,
    });
    isFirstContent = false;
  }

  openPdfBlob(pdf);
}

export function openPdfBlob(pdf: jsPDF) {
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

export async function openDomPdf(
  element: HTMLElement,
  prepareClone: PrepareCloneFn
): Promise<void> {
  const { html2canvas, jsPDF: JsPDF } = await loadPdfLibs();
  const pageElements = Array.from(
    element.querySelectorAll<HTMLElement>("[data-pdf-page]")
  ).filter((page) => !isPdfPageEmpty(page));

  const pdf = new JsPDF({ orientation: "p", unit: "pt", format: "a4" });
  let isFirstContent = true;

  if (pageElements.length === 0) {
    const capture = await captureElement(html2canvas, element, prepareClone);
    appendCanvasToPdf(pdf, capture, {
      newPageBefore: false,
      isFirstContent: true,
    });
  } else {
    for (const pageElement of pageElements) {
      const capture = await captureElement(html2canvas, pageElement, prepareClone);
      appendCanvasToPdf(pdf, capture, {
        newPageBefore: true,
        isFirstContent,
      });
      isFirstContent = false;
    }
  }

  openPdfBlob(pdf);
}
