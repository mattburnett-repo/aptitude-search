import { isPdfPageEmpty, openPackedDomPdf } from "./exportDomPdf";

function prepareAptitudeProfileCloneForExport(_doc: Document, clone: HTMLElement) {
  clone.classList.add("aptitude-profile", "aptitude-profile--pdf-export");
  for (const node of clone.querySelectorAll("details")) {
    if (node instanceof HTMLDetailsElement) {
      node.open = true;
    }
  }
}

function buildAptitudeProfilePages(source: HTMLElement): {
  staging: HTMLElement;
  pages: HTMLElement[];
} {
  const width = source.offsetWidth;
  const staging = document.createElement("div");
  staging.style.cssText = [
    "position:fixed",
    "left:-10000px",
    "top:0",
    `width:${width}px`,
    "pointer-events:none",
  ].join(";");
  document.body.appendChild(staging);

  const working = source.cloneNode(true) as HTMLElement;
  prepareAptitudeProfileCloneForExport(document, working);
  staging.appendChild(working);
  void working.offsetHeight;

  const pages = Array.from(
    working.querySelectorAll<HTMLElement>("[data-pdf-page]")
  ).filter((page) => !isPdfPageEmpty(page));

  return { staging, pages };
}

export async function openAptitudeProfilePdf(element: HTMLElement): Promise<void> {
  const { staging, pages } = buildAptitudeProfilePages(element);

  try {
    await openPackedDomPdf(pages, prepareAptitudeProfileCloneForExport);
  } finally {
    staging.remove();
  }
}
