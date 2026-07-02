import { bmcButtonConfig } from "../lib/bmcButtonConfig";
import { hasSupportLink, supportUrl } from "../config/support";

function BuyMeCoffeeIcon() {
  return (
    <svg
      className="bmc-btn-icon"
      viewBox="0 0 32 32"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        className="logo-outline"
        fill={bmcButtonConfig.outlineColor}
        d="M8 11h15v11c0 2.2-1.8 4-4 4H10c-2.2 0-4-1.8-4-4V11zm17 3h2.5a3.5 3.5 0 0 1 0 7H25"
      />
      <path
        className="logo-coffee"
        fill={bmcButtonConfig.coffeeColor}
        d="M10 13h13v9c0 1.1-.9 2-2 2H12c-1.1 0-2-.9-2-2v-9z"
      />
    </svg>
  );
}

export function BuyMeACoffeeButton() {
  if (!hasSupportLink) {
    return null;
  }

  return (
    <div className="site-footer-bmc">
      <div className="bmc-btn-container">
        <a
          className="bmc-btn"
          href={supportUrl}
          target="_blank"
          rel="noopener noreferrer"
        >
          <BuyMeCoffeeIcon />
          <span className="bmc-btn-text">{bmcButtonConfig.text}</span>
        </a>
      </div>
    </div>
  );
}
