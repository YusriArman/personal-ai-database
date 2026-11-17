import { describe, expect, it } from "vitest";
import { parseBlocks, splitCitations, splitMarks, splitWikilinks } from "./text";

describe("splitMarks", () => {
  it("turns only the server's mark tags into highlights", () => {
    expect(splitMarks("a <mark>b</mark> c <script>x</script>")).toEqual([
      { kind: "text", text: "a " },
      { kind: "mark", text: "b" },
      { kind: "text", text: " c <script>x</script>" },
    ]);
  });
  it("handles a snippet with no marks", () => {
    expect(splitMarks("plain")).toEqual([{ kind: "text", text: "plain" }]);
    expect(splitMarks("")).toEqual([]);
  });
});

describe("splitCitations", () => {
  it("makes citations only from valid numbers", () => {
    expect(splitCitations("Yes [1], no [7].", [1])).toEqual([
      { kind: "text", text: "Yes " },
      { kind: "cite", number: 1 },
      { kind: "text", text: ", no [7]." },
    ]);
  });
});

describe("splitWikilinks", () => {
  it("reads plain, aliased, heading and embedded links", () => {
    expect(splitWikilinks("see [[A]] and [[B C|the alias]] and [[D#Part]] ![[E]]")).toEqual([
      { kind: "text", text: "see " },
      { kind: "link", target: "A", label: "A" },
      { kind: "text", text: " and " },
      { kind: "link", target: "B C", label: "the alias" },
      { kind: "text", text: " and " },
      { kind: "link", target: "D", label: "D" },
      { kind: "text", text: " " },
      { kind: "link", target: "E", label: "E" },
    ]);
  });
});

describe("parseBlocks", () => {
  it("reads headings, checkboxes, code and paragraphs", () => {
    const body = "# Title\n\nline one\nline two\n\n- [ ] open\n- [x] done\n- plain\n```\n# not a heading\n```\n";
    expect(parseBlocks(body)).toEqual([
      { kind: "heading", level: 1, text: "Title" },
      { kind: "paragraph", text: "line one line two" },
      { kind: "item", text: "open", checkbox: "open" },
      { kind: "item", text: "done", checkbox: "done" },
      { kind: "item", text: "plain", checkbox: "none" },
      { kind: "code", text: "# not a heading" },
    ]);
  });
});
