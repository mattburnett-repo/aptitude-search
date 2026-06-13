import { useRef, type ReactNode } from "react";

type ClearFieldButtonProps = {
  ariaLabel: string;
  onClick: () => void;
};

export function ClearFieldButton({ ariaLabel, onClick }: ClearFieldButtonProps) {
  return (
    <button
      type="button"
      className="field-clear"
      aria-label={ariaLabel}
      onClick={onClick}
    >
      <svg viewBox="0 0 20 20" aria-hidden="true">
        <circle cx="10" cy="10" r="8.25" fill="none" stroke="currentColor" strokeWidth="1.5" />
        <path
          d="M7.25 7.25l5.5 5.5M12.75 7.25l-5.5 5.5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
      </svg>
    </button>
  );
}

type FieldWithClearProps = {
  showClear: boolean;
  onClear: () => void;
  clearLabel: string;
  children: ReactNode;
  variant?: "default" | "select";
};

export function FieldWithClear({
  showClear,
  onClear,
  clearLabel,
  children,
  variant = "default",
}: FieldWithClearProps) {
  const className = [
    "field-with-clear",
    variant === "select" ? "field-with-clear-select" : "",
    showClear ? "field-with-clear-active" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={className}>
      {children}
      {showClear ? <ClearFieldButton ariaLabel={clearLabel} onClick={onClear} /> : null}
    </div>
  );
}

type ClearInputProps = {
  id: string;
  value: string;
  onChange: (value: string) => void;
  clearLabel: string;
};

export function ClearInput({ id, value, onChange, clearLabel }: ClearInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const hasValue = value.trim().length > 0;

  function handleClear() {
    onChange("");
    inputRef.current?.focus();
  }

  return (
    <FieldWithClear showClear={hasValue} onClear={handleClear} clearLabel={clearLabel}>
      <input
        ref={inputRef}
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </FieldWithClear>
  );
}

type ClearSelectProps = {
  id: string;
  value: string;
  defaultValue: string;
  onChange: (value: string) => void;
  clearLabel: string;
  children: ReactNode;
};

export function ClearSelect({
  id,
  value,
  defaultValue,
  onChange,
  clearLabel,
  children,
}: ClearSelectProps) {
  const selectRef = useRef<HTMLSelectElement>(null);
  const showClear = value !== defaultValue;

  function handleClear() {
    onChange(defaultValue);
    selectRef.current?.focus();
  }

  return (
    <FieldWithClear
      showClear={showClear}
      onClear={handleClear}
      clearLabel={clearLabel}
      variant="select"
    >
      <select
        ref={selectRef}
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {children}
      </select>
    </FieldWithClear>
  );
}
