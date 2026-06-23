import {
  isPdfPageEmpty,
  maxSourceHeightPx,
  openPackedDomPdf,
} from "./exportDomPdf";

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

function prepareAptitudeProfileCloneForExport(doc: Document, clone: HTMLElement) {
  clone.classList.add("aptitude-profile", "aptitude-profile--pdf-export");
  flattenInferenceConfidenceForExport(doc, clone);
  for (const node of clone.querySelectorAll("details")) {
    if (node instanceof HTMLDetailsElement) {
      node.open = true;
    }
  }
}

function mergeInferenceConfidenceIfFits(
  pages: HTMLElement[],
  maxPageHeight: number
): HTMLElement[] {
  if (pages.length < 2) return pages;

  const rationalePage = pages.at(-2);
  const inferencePage = pages.at(-1);
  if (!rationalePage || !inferencePage) return pages;

  const inference = inferencePage.querySelector<HTMLElement>(
    ".aptitude-inference-confidence-pdf"
  );
  if (!inference) return pages;

  inference.classList.add("aptitude-inference-confidence-pdf--follows-content");
  rationalePage.appendChild(inference);
  void rationalePage.offsetHeight;

  if (rationalePage.getBoundingClientRect().height <= maxPageHeight) {
    inferencePage.remove();
    return pages.slice(0, -1);
  }

  rationalePage.removeChild(inference);
  inference.classList.remove("aptitude-inference-confidence-pdf--follows-content");
  return pages;
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

  const pages = mergeInferenceConfidenceIfFits(
    Array.from(working.querySelectorAll<HTMLElement>("[data-pdf-page]")).filter(
      (page) => !isPdfPageEmpty(page)
    ),
    maxSourceHeightPx(width)
  );

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
