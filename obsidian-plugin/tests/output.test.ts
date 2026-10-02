import { describe, expect, it } from "vitest";
import { prepareOutput } from "../src/core/output";

describe("prepareOutput", () => {
	it("strips a whole-output ```markdown fence", () => {
		expect(prepareOutput("```markdown\nSome retro.\n```", "r2025-01-02")).toBe(
			"# r2025-01-02\n\nSome retro."
		);
	});

	it("keeps inner/partial fences", () => {
		const out = prepareOutput(
			"Intro\n```markdown\nsnippet\n```\nOutro",
			"r2025-01-02"
		);
		expect(out).toBe("# r2025-01-02\n\nIntro\n```markdown\nsnippet\n```\nOutro");
	});

	it("keeps fences of other languages at the start", () => {
		const out = prepareOutput("```text\nnot markdown\n```", "r2025-01-02");
		expect(out).toBe("# r2025-01-02\n\n```text\nnot markdown\n```");
	});

	it("matches MARKDOWN_RE.match semantics: anchored at start, not at end", () => {
		// Python's re.match only anchors the beginning; trailing text after the
		// first closing fence is dropped with the fence.
		expect(
			prepareOutput("```markdown\nbody\n```\ntrailing", "r2025-01-02")
		).toBe("# r2025-01-02\n\nbody");
	});

	it("replaces ![[ embeds with [[ links", () => {
		expect(prepareOutput("See ![[page]] and ![[img.png]].", "r1")).toBe(
			"# r1\n\nSee [[page]] and [[img.png]]."
		);
	});

	it("trims the model output and prepends the H1 with a blank line", () => {
		expect(prepareOutput("\n\n  Body text.  \n", "r2025-12-31")).toBe(
			"# r2025-12-31\n\nBody text."
		);
	});
});
