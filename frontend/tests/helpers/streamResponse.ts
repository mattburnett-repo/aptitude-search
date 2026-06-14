export function mockNdjsonStreamResponse(
  lines: string[],
  init: ResponseInit = { status: 200 }
): Response {
  const body = lines.length > 0 ? `${lines.join("\n")}\n` : "";
  const encoder = new TextEncoder();
  let offset = 0;
  const chunkSize = 24;

  const stream = new ReadableStream<Uint8Array>({
    pull(controller) {
      if (offset >= body.length) {
        controller.close();
        return;
      }
      controller.enqueue(
        encoder.encode(body.slice(offset, offset + chunkSize))
      );
      offset += chunkSize;
    },
  });

  return new Response(stream, init);
}
