/** Small pure text helpers, kept out of components so they can be unit-tested. */

export type Segment =
  | { kind: "text"; text: string }
  | { kind: "mark"; text: string }
  | { kind: "cite"; number: number }
  | { kind: "link"; target: string; label: string };

/**
 * Split a search snippet on the <mark>…</mark> pairs the server inserts.
 * The snippet comes from note text, which may itself contain HTML, so it is never
 * injected as HTML: only the server's own mark tags become highlights.
 */
export function splitMarks(snippet: string): Segment[] {
  const out: Segment[] = [];
  const pattern = /<mark>(.*?)<\/mark>/gs;
  let last = 0;
  for (const match of snippet.matchAll(pattern)) {
    if (match.index > last) out.push({ kind: "text", text: snippet.slice(last, match.index) });
    out.push({ kind: "mark", text: match[1] });
    last = match.index + match[0].length;
  }
  if (last < snippet.length) out.push({ kind: "text", text: snippet.slice(last) });
  return out;
}

/** Split an answer into text and [n] citations. Only numbers in `valid` become citations. */
export function splitCitations(answer: string, valid: number[]): Segment[] {
  const out: Segment[] = [];
  const pattern = /\[(\d+)\]/g;
  let last = 0;
  for (const match of answer.matchAll(pattern)) {
    const number = Number(match[1]);
    if (!valid.includes(number)) continue;
    if (match.index > last) out.push({ kind: "text", text: answer.slice(last, match.index) });
    out.push({ kind: "cite", number });
    last = match.index + match[0].length;
  }
  if (last < answer.length) out.push({ kind: "text", text: answer.slice(last) });
  return out;
}

/** Split a line of note text into plain text and [[wikilinks]]. */
export function splitWikilinks(line: string): Segment[] {
  const out: Segment[] = [];
  const pattern = /!?\[\[([^\]|#]+)(#[^\]|]*)?(?:\|([^\]]*))?\]\]/g;
  let last = 0;
  for (const match of line.matchAll(pattern)) {
    if (match.index > last) out.push({ kind: "text", text: line.slice(last, match.index) });
    const target = match[1].trim();
    out.push({ kind: "link", target, label: (match[3] ?? target).trim() });
    last = match.index + match[0].length;
  }
  if (last < line.length) out.push({ kind: "text", text: line.slice(last) });
  return out;
}

export type Block =
  | { kind: "heading"; level: number; text: string }
  | { kind: "item"; text: string; checkbox: "none" | "open" | "done" }
  | { kind: "code"; text: string }
  | { kind: "paragraph"; text: string };

/** A deliberately small markdown reader: headings, list items, checkboxes, code, paragraphs. */
export function parseBlocks(body: string): Block[] {
  const blocks: Block[] = [];
  let code: string[] | null = null;
  let paragraph: string[] = [];
  const flush = () => {
    if (paragraph.length) blocks.push({ kind: "paragraph", text: paragraph.join(" ") });
    paragraph = [];
  };
  for (const line of body.split("\n")) {
    if (/^\s*(```|~~~)/.test(line)) {
      if (code === null) {
        flush();
        code = [];
      } else {
        blocks.push({ kind: "code", text: code.join("\n") });
        code = null;
      }
      continue;
    }
    if (code !== null) {
      code.push(line);
      continue;
    }
    const heading = /^(#{1,6})\s+(.*\S)\s*$/.exec(line);
    const item = /^\s*(?:[-*+]|\d+\.)\s+(?:\[( |x|X)\]\s+)?(.*)$/.exec(line);
    if (heading) {
      flush();
      blocks.push({ kind: "heading", level: heading[1].length, text: heading[2] });
    } else if (item) {
      flush();
      const checkbox = item[1] === undefined ? "none" : item[1] === " " ? "open" : "done";
      blocks.push({ kind: "item", text: item[2], checkbox });
    } else if (line.trim() === "") {
      flush();
    } else {
      paragraph.push(line.trim());
    }
  }
  if (code !== null) blocks.push({ kind: "code", text: code.join("\n") });
  flush();
  return blocks;
}
