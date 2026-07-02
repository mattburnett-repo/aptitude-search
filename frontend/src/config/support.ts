const url = import.meta.env.VITE_SUPPORT_URL?.trim() ?? "";

export const supportUrl = url;
export const hasSupportLink = url.length > 0;

const bmcSlugMatch = /^https:\/\/buymeacoffee\.com\/([^/?#]+)\/?$/i.exec(url);

export const supportSlug = bmcSlugMatch?.[1] ?? "";
