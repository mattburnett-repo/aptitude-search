import type { ReactNode } from "react";
import { hasSupportLink, supportUrl } from "../config/support";

export function SupportLink({ children }: { children: ReactNode }) {
  if (!hasSupportLink) {
    return <>{children}</>;
  }

  return (
    <a
      className="support-link"
      href={supportUrl}
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
    </a>
  );
}
