import type { PipelineResult } from "../api/pipeline";

export function exportPipelineResult(result: PipelineResult) {
  const blob = new Blob([JSON.stringify(result, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "aptitude-search-results.json";
  a.click();
  URL.revokeObjectURL(url);
}

export async function copyVerifiedMatches(result: PipelineResult) {
  if (!result.verified_matches) return;
  await navigator.clipboard.writeText(
    JSON.stringify(result.verified_matches, null, 2)
  );
}
