import { useEffect, useState } from "react";

const PHOTON = "https://photon.komoot.io/api/";

function formatLabel(props: Record<string, string | undefined>): string {
  const parts: string[] = [];
  const name = (props.name || props.city || "").trim();
  if (name) parts.push(name);
  const state = (props.state || "").trim();
  if (state && !parts.includes(state)) parts.push(state);
  const country = (props.country || "").trim();
  if (country && !parts.includes(country)) parts.push(country);
  return parts.join(", ");
}

async function fetchLocations(q: string): Promise<string[]> {
  const url = new URL(PHOTON);
  url.searchParams.set("q", q);
  url.searchParams.set("limit", "8");
  for (const layer of ["city", "locality", "district"]) {
    url.searchParams.append("layer", layer);
  }

  const res = await fetch(url);
  if (!res.ok) return [];

  const data = (await res.json()) as {
    features?: { properties?: Record<string, string | undefined> }[];
  };

  const seen = new Set<string>();
  const labels: string[] = [];
  for (const feature of data.features ?? []) {
    const label = formatLabel(feature.properties ?? {});
    if (label && !seen.has(label)) {
      seen.add(label);
      labels.push(label);
    }
  }
  return labels;
}

type LocationInputProps = {
  id: string;
  value: string;
  onChange: (value: string) => void;
};

export function LocationInput({ id, value, onChange }: LocationInputProps) {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const listId = `${id}-suggestions`;

  useEffect(() => {
    const q = value.trim();
    if (q.length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = window.setTimeout(() => {
      fetchLocations(q)
        .then(setSuggestions)
        .catch(() => setSuggestions([]));
    }, 300);
    return () => window.clearTimeout(timer);
  }, [value]);

  return (
    <>
      <input
        id={id}
        list={listId}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        autoComplete="off"
      />
      <datalist id={listId}>
        {suggestions.map((label) => (
          <option key={label} value={label} />
        ))}
      </datalist>
    </>
  );
}
