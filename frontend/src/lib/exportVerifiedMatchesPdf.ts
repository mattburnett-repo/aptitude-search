import {
  appendCanvasToPdf,
  captureElement,
  isPdfPageEmpty,
  loadPdfLibs,
  openPdfBlob,
  PDF_MARGIN_PT,
} from "./exportDomPdf";

function prepareVerifiedMatchesCloneForExport(_doc: Document, clone: HTMLElement) {
  clone.classList.add("verified-matches", "verified-matches--pdf-export");
}

function maxSourceHeightPerPdfPage(sourceWidthPx: number): number {
  const pageWidth = 595.28;
  const pageHeight = 841.89;
  const contentWidth = pageWidth - PDF_MARGIN_PT * 2;
  const printableHeight = pageHeight - PDF_MARGIN_PT * 2;
  return (printableHeight * sourceWidthPx) / contentWidth;
}

function listGapPx(list: HTMLElement): number {
  const style = getComputedStyle(list);
  const gap = parseFloat(style.rowGap || style.gap);
  return Number.isFinite(gap) ? gap : 12;
}

function createPageShell(width: number): HTMLElement {
  const page = document.createElement("div");
  page.className = "verified-matches";
  page.style.width = `${width}px`;
  prepareVerifiedMatchesCloneForExport(document, page);
  return page;
}

function measurePageHeight(
  staging: HTMLElement,
  width: number,
  blocks: HTMLElement[]
): number {
  if (blocks.length === 0) return 0;

  const probe = createPageShell(width);
  for (const block of blocks) {
    probe.appendChild(block);
  }
  staging.appendChild(probe);
  void probe.offsetHeight;
  const height = probe.getBoundingClientRect().height;

  for (const block of blocks) {
    probe.removeChild(block);
  }
  staging.removeChild(probe);
  return height;
}

function fitsOnPage(
  page: HTMLElement,
  block: HTMLElement,
  maxPageHeight: number
): boolean {
  page.appendChild(block);
  void page.offsetHeight;
  const fits = page.getBoundingClientRect().height <= maxPageHeight;
  if (!fits) {
    page.removeChild(block);
  }
  return fits;
}

type MeasuredCard = {
  element: HTMLElement;
  height: number;
};

function measureJobCards(list: HTMLElement): MeasuredCard[] {
  return Array.from(list.querySelectorAll<HTMLElement>(".job-card")).map((element) => ({
    element,
    height: element.getBoundingClientRect().height,
  }));
}

type PackedPage = {
  leading: HTMLElement[];
  cards: MeasuredCard[];
};

function buildVerifiedMatchesPages(source: HTMLElement): {
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
  prepareVerifiedMatchesCloneForExport(document, working);
  staging.appendChild(working);
  void working.offsetHeight;

  const maxPageHeight = maxSourceHeightPerPdfPage(width);
  const pages: HTMLElement[] = [];

  const searchSection = working
    .querySelector(".verified-search-plan")
    ?.closest<HTMLElement>(".verified-section");
  if (searchSection) {
    searchSection.remove();
  }

  const notesSection = working
    .querySelector(".verified-notes")
    ?.closest<HTMLElement>(".verified-section");
  if (notesSection) {
    notesSection.remove();
  }

  const resultsSection = working
    .querySelector(".job-card-list")
    ?.closest<HTMLElement>(".verified-section");

  const initialLeading: HTMLElement[] = [];
  if (searchSection && !isPdfPageEmpty(searchSection)) {
    initialLeading.push(searchSection);
  }

  if (resultsSection) {
    const list = resultsSection.querySelector<HTMLElement>(".job-card-list");
    const cards = list ? measureJobCards(list) : [];

    const header = document.createElement("div");
    header.className = "verified-results-header";
    for (const child of Array.from(resultsSection.children)) {
      if (child === list) continue;
      header.appendChild(child);
    }
    resultsSection.remove();
    list?.remove();

    if (header.childNodes.length > 0) {
      initialLeading.push(header);
    }

    const gap = list ? listGapPx(list) : 12;

    if (cards.length === 0) {
      const page = createPageShell(width);
      for (const block of initialLeading) {
        page.appendChild(block);
      }
      staging.appendChild(page);
      pages.push(page);
    } else {
      const measureLeading = (blocks: HTMLElement[]) =>
        measurePageHeight(staging, width, blocks);

      const packedPages: PackedPage[] = [];
      let cardIndex = 0;
      let leading = initialLeading;

      while (cardIndex < cards.length) {
        const leadingHeight = measureLeading(leading);
        let used = leadingHeight + (leading.length > 0 && cards.length > 0 ? gap : 0);
        const pageCards: MeasuredCard[] = [];

        while (cardIndex < cards.length) {
          const gapBefore = pageCards.length > 0 ? gap : 0;
          const needed = gapBefore + cards[cardIndex].height;

          if (pageCards.length > 0 && used + needed > maxPageHeight) {
            break;
          }

          if (pageCards.length === 0 && used + needed > maxPageHeight) {
            if (used > 0) {
              break;
            }
            pageCards.push(cards[cardIndex]);
            cardIndex += 1;
            break;
          }

          pageCards.push(cards[cardIndex]);
          used += needed;
          cardIndex += 1;
        }

        if (pageCards.length === 0 && leading.length === 0) {
          break;
        }

        packedPages.push({ leading, cards: pageCards });
        leading = [];
      }

      if (leading.length > 0) {
        packedPages.push({ leading, cards: [] });
      }

      for (const packed of packedPages) {
        const page = createPageShell(width);
        for (const block of packed.leading) {
          page.appendChild(block);
        }
        if (packed.cards.length > 0) {
          const cardList = document.createElement("div");
          cardList.className = "job-card-list";
          for (const card of packed.cards) {
            cardList.appendChild(card.element);
          }
          page.appendChild(cardList);
        }
        staging.appendChild(page);
        pages.push(page);
      }
    }
  } else if (initialLeading.length > 0) {
    const page = createPageShell(width);
    for (const block of initialLeading) {
      page.appendChild(block);
    }
    staging.appendChild(page);
    pages.push(page);
  }

  if (notesSection && !isPdfPageEmpty(notesSection)) {
    notesSection.style.marginTop = "1.25rem";
    const lastPage = pages.at(-1);

    if (lastPage && fitsOnPage(lastPage, notesSection, maxPageHeight)) {
      // notes appended to last page
    } else {
      const page = createPageShell(width);
      page.appendChild(notesSection);
      staging.appendChild(page);
      pages.push(page);
    }
  }

  working.remove();
  return { staging, pages };
}

export async function openVerifiedMatchesPdf(element: HTMLElement): Promise<void> {
  const { html2canvas, jsPDF: JsPDF } = await loadPdfLibs();
  const { staging, pages } = buildVerifiedMatchesPages(element);

  try {
    const pdf = new JsPDF({ orientation: "p", unit: "pt", format: "a4" });
    let isFirstContent = true;

    for (const pageElement of pages.filter((page) => !isPdfPageEmpty(page))) {
      const capture = await captureElement(
        html2canvas,
        pageElement,
        prepareVerifiedMatchesCloneForExport
      );
      appendCanvasToPdf(pdf, capture, {
        newPageBefore: true,
        isFirstContent,
      });
      isFirstContent = false;
    }

    openPdfBlob(pdf);
  } finally {
    staging.remove();
  }
}
