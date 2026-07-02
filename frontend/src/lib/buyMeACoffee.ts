const BMC_SCRIPT_SRC =
  "https://cdnjs.buymeacoffee.com/1.0.0/button.prod.min.js";
const BMC_SCRIPT_ID = "bmc-button-script";

export const bmcButtonConfig = {
  text: "Buy me a coffee",
  color: "#40DCA5",
  emoji: "☕",
  font: "Cookie",
  fontColor: "#ffffff",
  outlineColor: "#000000",
  coffeeColor: "#FFDD00",
} as const;

let scriptLoadPromise: Promise<void> | null = null;

function loadBuyMeACoffeeScript(): Promise<void> {
  if (typeof window.bmcBtnWidget === "function") {
    return Promise.resolve();
  }

  if (scriptLoadPromise) {
    return scriptLoadPromise;
  }

  scriptLoadPromise = new Promise((resolve, reject) => {
    const existing = document.getElementById(
      BMC_SCRIPT_ID,
    ) as HTMLScriptElement | null;

    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener(
        "error",
        () => reject(new Error("Failed to load Buy Me a Coffee button script.")),
        { once: true },
      );
      return;
    }

    const script = document.createElement("script");
    script.id = BMC_SCRIPT_ID;
    script.src = BMC_SCRIPT_SRC;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () =>
      reject(new Error("Failed to load Buy Me a Coffee button script."));
    document.head.appendChild(script);
  });

  return scriptLoadPromise;
}

export async function renderBuyMeACoffeeButton(
  container: HTMLElement,
  slug: string,
): Promise<void> {
  await loadBuyMeACoffeeScript();

  if (typeof window.bmcBtnWidget !== "function") {
    throw new Error("Buy Me a Coffee button script did not initialize.");
  }

  container.innerHTML = window.bmcBtnWidget(
    bmcButtonConfig.text,
    slug,
    bmcButtonConfig.color,
    bmcButtonConfig.emoji,
    bmcButtonConfig.font,
    bmcButtonConfig.fontColor,
    bmcButtonConfig.outlineColor,
    bmcButtonConfig.coffeeColor,
  );
}
