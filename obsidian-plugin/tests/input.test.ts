import { describe, expect, it } from "vitest";
import {
	frontmatterOf,
	prepareInput,
	stripCodeBlocks,
	stripFrontmatter,
	stripSections,
} from "../src/core/input";

describe("stripFrontmatter", () => {
	it("removes frontmatter when the file opens with ---", () => {
		const text = "---\nstress: 7\n---\nBody text.\n";
		expect(stripFrontmatter(text)).toBe("Body text.\n");
	});

	it("leaves text without an opening --- untouched", () => {
		const text = "No frontmatter here.\nJust text.\n";
		expect(stripFrontmatter(text)).toBe(text);
	});

	it("does not treat a spaced or longer dash line as frontmatter", () => {
		const text = "--- spaced\nbody\n---\n";
		expect(stripFrontmatter(text)).toBe(text);
		const four = "----\nbody\n---\n";
		expect(stripFrontmatter(four)).toBe(four);
	});

	it("requires the closing fence to be followed by a newline", () => {
		const text = "---\nkey: 1\n---";
		expect(stripFrontmatter(text)).toBe(text);
	});

	it("removes a later line-anchored --- block, matching the Python sub() semantics", () => {
		// FRONTMATTER_RE uses MULTILINE: ^ matches at any line start, and
		// Python applies it with re.sub (not only at the start of the file).
		const text = "Intro.\n---\nkey: 1\n---\nRest.\n";
		expect(stripFrontmatter(text)).toBe("Intro.\nRest.\n");
	});
});

describe("stripCodeBlocks", () => {
	it("removes language-tagged fenced blocks and the preceding newline", () => {
		const text = "Before.\n```python\nprint('hi')\n```\nAfter.\n";
		expect(stripCodeBlocks(text)).toBe("Before.After.\n");
	});

	it("keeps bare fences", () => {
		const text = "Before.\n```\nplain block\n```\nAfter.\n";
		expect(stripCodeBlocks(text)).toBe(text);
	});

	it("keeps fences whose tag is not lowercase letters only", () => {
		// [a-z]+ does not match "python3" or "c++".
		const text = "```python3\nx\n```\n";
		expect(stripCodeBlocks("\n" + text)).toBe("\n" + text);
	});

	it("keeps a fence at the very start of the file (needs a preceding newline)", () => {
		const text = "```python\nx\n```\nrest\n";
		expect(stripCodeBlocks(text)).toBe(text);
	});

	it("keeps inline code", () => {
		const text = "Use `npm test` here.\n";
		expect(stripCodeBlocks(text)).toBe(text);
	});
});

describe("stripSections", () => {
	it("removes a matching section case-insensitively, including subsections", () => {
		const text = [
			"# Morning",
			"kept 1",
			"## PRIVATE",
			"secret",
			"### Details",
			"more secret",
			"## Evening",
			"kept 2",
			"",
		].join("\n");
		expect(stripSections(text, ["private"])).toBe(
			"# Morning\nkept 1\n## Evening\nkept 2\n"
		);
	});

	it("stops removal at a same-or-higher-level heading", () => {
		const text = "## Ignored\nsecret\n# Next\nkept\n";
		expect(stripSections(text, ["ignored"])).toBe("# Next\nkept\n");
	});

	it("keeps skipping when the next same-level heading is also ignored", () => {
		const text =
			"# A\nsecret a\n# B\nsecret b\n# C\nkept\n";
		expect(stripSections(text, ["a", "b"])).toBe("# C\nkept\n");
	});

	it("matches headings with surrounding whitespace and trailing spaces", () => {
		const text = "##   Private   \nsecret\n## Other\nkept\n";
		expect(stripSections(text, ["private"])).toBe("## Other\nkept\n");
	});

	it("returns the text unchanged when no headers are given", () => {
		const text = "# A\nbody\n";
		expect(stripSections(text, [])).toBe(text);
		expect(stripSections(text, ["  ", ""])).toBe(text);
	});

	it("ignores entries with surrounding whitespace", () => {
		const text = "# Secret\nx\n# Kept\ny\n";
		expect(stripSections(text, ["  secret  "])).toBe("# Kept\ny\n");
	});
});

describe("frontmatterOf", () => {
	it("parses simple scalar values", () => {
		const text =
			"---\nstress: 7\nkg: 81.5\nmood: good\nmeditation: '10 min'\nrelax: true\n---\nBody\n";
		expect(frontmatterOf(text)).toEqual({
			stress: 7,
			kg: 81.5,
			mood: "good",
			meditation: "10 min",
			relax: true,
		});
	});

	it("returns an empty record when the file does not open with ---", () => {
		expect(frontmatterOf("Body\n---\nkey: 1\n---\n")).toEqual({});
		expect(frontmatterOf("no frontmatter")).toEqual({});
	});

	it("stores null for empty values and skips nested lines", () => {
		const text = "---\nempty:\nnested:\n  inner: 1\n---\n";
		expect(frontmatterOf(text)).toEqual({ empty: null, nested: null });
	});
});

describe("prepareInput", () => {
	const metrics: [string, string][] = [
		["stress", "Stress level {} of 10."],
		["kg", "Weight {} kg."],
		["mood", "Mood: {}"],
	];

	it("prefixes with Page: [[name]]", () => {
		const out = prepareInput("2025-01-02", "Just a body.\n");
		expect(out).toBe("Page: [[2025-01-02]]\nJust a body.\n");
	});

	it("cleans frontmatter, tagged code blocks and ignored sections", () => {
		const raw =
			"---\nstress: 5\n---\n# Day\nkept\n## Private\nsecret\n## Other\nalso kept\n```python\nx\n```\n";
		const out = prepareInput("2025-01-02", raw, {
			ignoredHeaders: ["private"],
		});
		expect(out).toBe(
			"Page: [[2025-01-02]]\n# Day\nkept\n## Other\nalso kept"
		);
	});

	it("glues the lines around a removed code block, matching CODEBLOCKS_RE", () => {
		// The Python regex consumes the newline preceding the fence, so the
		// lines before and after the block end up adjacent.
		const raw = "# Day\nkept\n```python\nx\n```\n## Private\nsecret\n";
		const out = prepareInput("2025-01-02", raw, {
			ignoredHeaders: ["private"],
		});
		expect(out).toBe("Page: [[2025-01-02]]\n# Day\nkept## Private\nsecret\n");
	});

	it("appends metric lines in metric-table order, not frontmatter order", () => {
		// The cleaned content keeps its trailing newline, so the first metric
		// line follows a blank line, as in Python's "\n".join().
		const raw = "---\nmood: calm\nstress: 7\n---\nBody\n";
		const out = prepareInput("2025-01-02", raw, { metrics });
		expect(out).toBe(
			"Page: [[2025-01-02]]\nBody\n\nStress level 7 of 10.\nMood: calm"
		);
	});

	it("skips metric keys missing from the frontmatter", () => {
		const raw = "---\nkg: 80.5\n---\nBody\n";
		const out = prepareInput("2025-01-02", raw, { metrics });
		expect(out).toBe("Page: [[2025-01-02]]\nBody\n\nWeight 80.5 kg.");
	});

	it("appends no metrics when there is no frontmatter", () => {
		const out = prepareInput("2025-01-02", "Body\n", { metrics });
		expect(out).toBe("Page: [[2025-01-02]]\nBody\n");
	});

	it("skips frontmatter keys with empty (null) values", () => {
		const raw = "---\nstress:\n---\nBody\n";
		const out = prepareInput("2025-01-02", raw, { metrics });
		expect(out).toBe("Page: [[2025-01-02]]\nBody\n");
	});
});
