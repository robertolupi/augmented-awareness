import { describe, expect, it } from "vitest";
import {
	buildTagsBlock,
	canonicalTagNames,
	normalizeTags,
	renderRetroPrompt,
	renderTemplate,
} from "../src/core/prompts";

import dailyPrompt from "../src/prompts/daily.md";

describe("renderTemplate", () => {
	const tpl =
		"start\n{% if tags %}has: {{ block }}{% else %}none{% endif %}\nend";

	it("renders the if branch when the variable is truthy", () => {
		expect(renderTemplate(tpl, { tags: ["a"], block: "- #a" })).toBe(
			"start\nhas: - #a\nend"
		);
	});

	it("renders the else branch for empty arrays and missing variables", () => {
		expect(renderTemplate(tpl, { tags: [], block: "x" })).toBe(
			"start\nnone\nend"
		);
		expect(renderTemplate(tpl, { block: "x" })).toBe("start\nnone\nend");
		expect(renderTemplate(tpl, { tags: "", block: "x" })).toBe(
			"start\nnone\nend"
		);
	});

	it("interpolates variables and renders missing ones as empty", () => {
		expect(renderTemplate("a {{ x }} b {{ y }} c", { x: "1" })).toBe(
			"a 1 b  c"
		);
	});

	it("supports if without else", () => {
		expect(renderTemplate("{% if x %}yes{% endif %}!", { x: true })).toBe(
			"yes!"
		);
		expect(renderTemplate("{% if x %}yes{% endif %}!", {})).toBe("!");
	});
});

describe("tag normalization", () => {
	it("lowercases, trims and replaces spaces with underscores", () => {
		expect(
			normalizeTags({ "Mental Health": "mind", "  Work ": "job" })
		).toEqual({ mental_health: "mind", work: "job" });
	});

	it("drops empty tags and trims descriptions", () => {
		expect(normalizeTags({ "   ": "x", ok: "  desc  " })).toEqual({
			ok: "desc",
		});
	});

	it("sorts canonical tag names", () => {
		expect(canonicalTagNames({ beta: "", Alpha: "" })).toEqual([
			"alpha",
			"beta",
		]);
	});
});

describe("buildTagsBlock", () => {
	it("formats - #tag: description lines sorted by normalized tag", () => {
		const block = buildTagsBlock({
			Health: "physical or mental health",
			"deep work": "focused work",
			plain: "",
		});
		expect(block).toBe(
			"- #deep_work: focused work\n- #health: physical or mental health\n- #plain"
		);
	});

	it("returns an empty string with no tags", () => {
		expect(buildTagsBlock({})).toBe("");
	});
});

describe("bundled daily prompt", () => {
	it("includes the tags block when canonical tags exist", () => {
		const tags = { Health: "mind and body" };
		const rendered = renderTemplate(dailyPrompt, {
			canonical_tags: canonicalTagNames(tags),
			canonical_tags_block: buildTagsBlock(tags),
		});
		expect(rendered).toContain("- #health: mind and body");
		expect(rendered).not.toContain("No canonical tags configured.");
		expect(rendered).not.toContain("{%");
	});

	it("renders the else branch when no canonical tags exist", () => {
		const rendered = renderTemplate(dailyPrompt, {
			canonical_tags: [],
			canonical_tags_block: "",
		});
		expect(rendered).toContain("No canonical tags configured.");
		expect(rendered).not.toContain("{%");
	});
});

describe("renderRetroPrompt for all levels", () => {
	it("renders daily, weekly, monthly, yearly with canonical tags", () => {
		const tags = { Reflection: "daily thought" };
		for (const level of ["daily", "weekly", "monthly", "yearly"] as const) {
			const prompt = renderRetroPrompt(level, tags);
			expect(prompt).toContain("- #reflection: daily thought");
			expect(prompt).not.toContain("{%");
			expect(prompt).not.toContain("{{");
		}
	});

	it("renders daily, weekly, monthly, yearly without canonical tags", () => {
		for (const level of ["daily", "weekly", "monthly", "yearly"] as const) {
			const prompt = renderRetroPrompt(level, {});
			expect(prompt).toContain("No canonical tags configured.");
			expect(prompt).not.toContain("{%");
			expect(prompt).not.toContain("{{");
		}
	});
});

