const url = import.meta.env.VITE_SUPPORT_URL?.trim() ?? "";

export const supportUrl = url;
export const hasSupportLink = url.length > 0;
