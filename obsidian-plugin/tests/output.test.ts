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

	it("strips <think> reasoning wrappers from output", () => {
		const input = "<think>\nAnalyzing the day's events...\n- Meeting at 10\n- Stress level was high\n</think>\n\n# January 8 Summary\n\nEverything went well.";
		expect(prepareOutput(input, "r2025-01-08")).toBe(
			"# r2025-01-08\n\n# January 8 Summary\n\nEverything went well."
		);
	});

	it("strips <think> wrapper before a ```markdown fence", () => {
		const input = "<think>\nInternal thinking process.\n</think>\n```markdown\nActual retrospective text.\n```";
		expect(prepareOutput(input, "r2025-01-08")).toBe(
			"# r2025-01-08\n\nActual retrospective text."
		);
	});

	it("strips <think> wrapper inside a ```markdown fence", () => {
		const input = "```markdown\n<think>\nInner thinking process.\n</think>\nActual retrospective text.\n```";
		expect(prepareOutput(input, "r2025-01-08")).toBe(
			"# r2025-01-08\n\nActual retrospective text."
		);
	});

	it("strips multiple or case-insensitive <think> and <thought> tags", () => {
		const input = "<THINK>first think</THINK>\nIntro.\n<thought>second think</thought>\nOutro.";
		expect(prepareOutput(input, "r1")).toBe(
			"# r1\n\nIntro.\n\nOutro."
		);
	});

	it("strips <think> tag immediately followed by heading without newline", () => {
		const input =
			"<think>**Interpreting completed events**\n\nI need to interpret only completed events.\nTwo questions remain.</think>### 1 Key Events\n- None observed";
		expect(prepareOutput(input, "r2026-10-02")).toBe(
			"# r2026-10-02\n\n### 1 Key Events\n- None observed"
		);
	});
});
