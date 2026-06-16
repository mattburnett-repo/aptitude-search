const API_BASE = (import.meta.env.VITE_API_URL ?? "/api").replace(/\/$/, "");

export type PipelineResult = {
  aptitude_profile: unknown;
  verified_matches: unknown;
};

type StreamEvent =
  | { type: "progress"; message: string }
  | { type: "result"; data: PipelineResult }
  | { type: "error"; detail: string; request_id: string };

function formatErrorMessage(detail: string, requestId?: string): string {
  if (requestId) return `${detail} (ref: ${requestId})`;
  return detail;
}

function parseStreamLine(line: string): StreamEvent {
  return JSON.parse(line) as StreamEvent;
}

async function readErrorMessage(res: Response): Promise<string> {
  const raw = await res.text();
  if (!raw) return res.statusText;
  try {
    const data = JSON.parse(raw) as Record<string, unknown>;
    const requestId =
      typeof data.request_id === "string" ? data.request_id : undefined;
    if (typeof data.detail === "string") {
      return formatErrorMessage(data.detail, requestId);
    }
    if (typeof data.error === "string") {
      return formatErrorMessage(data.error, requestId);
    }
  } catch {
    return raw;
  }
  return res.statusText;
}

export async function runPipelineStream(
  body: unknown,
  onProgress: (message: string) => void
): Promise<PipelineResult> {
  const res = await fetch(`${API_BASE}/v1/pipeline?stream=1`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(await readErrorMessage(res));
  }

  const reader = res.body?.getReader();
  if (!reader) {
    throw new Error("No response body from server.");
  }

  const decoder = new TextDecoder();
  let buffer = "";
  let result: PipelineResult | null = null;

  const handleEvent = (event: StreamEvent) => {
    if (event.type === "progress") {
      onProgress(event.message);
      return;
    }
    if (event.type === "result") {
      result = event.data;
      return;
    }
    throw new Error(formatErrorMessage(event.detail, event.request_id));
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.trim()) continue;
      handleEvent(parseStreamLine(line));
    }
  }

  if (buffer.trim()) {
    handleEvent(parseStreamLine(buffer));
  }

  if (!result) {
    throw new Error("Pipeline finished without a result.");
  }

  return result;
}
