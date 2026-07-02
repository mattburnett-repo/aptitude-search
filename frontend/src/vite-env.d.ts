/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_SUPPORT_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

interface Window {
  bmcBtnWidget?: (
    text: string,
    slug: string,
    color: string,
    emoji: string,
    font: string,
    fontColor?: string,
    outlineColor?: string,
    coffeeColor?: string,
  ) => string;
}
