import { describe, expect, it } from "vitest";
import {
	DEFAULT_METRIC_TEMPLATES,
	DEFAULT_SETTINGS,
	getModelOptions,
	getProviderOptions,
	parseCanonicalTags,
	parseIgnoredHeadings,
	parseMetricTemplates,
} from "../src/settings";

describe("parseIgnoredHeadings", () => {
	it("splits lines and trims whitespace", () => {
		expect(parseIgnoredHeadings("Private\n  Health \n\nMood")).toEqual([
			"Private",
			"Health",
			"Mood",
		]);
	});

	it("returns an empty list for an empty setting", () => {
		expect(parseIgnoredHeadings("")).toEqual([]);
		expect(parseIgnoredHeadings("  \n \n")).toEqual([]);
	});
});

describe("parseMetricTemplates", () => {
	it("parses key = template lines preserving order", () => {
		expect(
			parseMetricTemplates(
				"stress = Stress level {} of 10.\nmood = Mood: {}"
			)
		).toEqual([
			["stress", "Stress level {} of 10."],
			["mood", "Mood: {}"],
		]);
	});

	it("splits on the first = only and skips malformed lines", () => {
		expect(
			parseMetricTemplates("a = x = y\nno separator\n= no key\nkey =")
		).toEqual([["a", "x = y"]]);
	});

	it("parses the default table into 15 entries in METRIC_FORMATTERS order", () => {
		const parsed = parseMetricTemplates(DEFAULT_METRIC_TEMPLATES);
		expect(parsed.map(([k]) => k)).toEqual([
			"stress",
			"kg",
			"bmi",
			"mood",
			"meditation",
			"relax",
			"career",
			"social",
			"exercise",
			"sleep_score",
			"vitals_score",
			"activity_score",
			"relax_score",
			"pushups",
			"exercise_time",
		]);
		expect(parsed[0][1]).toBe("Stress level {} of 10.");
	});
});

describe("parseCanonicalTags", () => {
	it("parses tag: description lines", () => {
		expect(
			parseCanonicalTags("health: mind and body\nwork: job stuff")
		).toEqual({ health: "mind and body", work: "job stuff" });
	});

	it("treats a line without : as a tag with empty description", () => {
		expect(parseCanonicalTags("plain\nother: desc")).toEqual({
			plain: "",
			other: "desc",
		});
	});

	it("keeps colons inside descriptions", () => {
		expect(parseCanonicalTags("tag: desc: with colon")).toEqual({
			tag: "desc: with colon",
		});
	});

	it("returns an empty record for an empty setting", () => {
		expect(parseCanonicalTags("")).toEqual({});
	});
});

describe("settings defaults", () => {
	it("defaults the new fields when absent from stored data", () => {
		// Simulates the dev vault's milestone-1 data.json, which only has the
		// four original keys.
		const stored = {
			providerId: "123",
			model: "echo-model",
			journalDir: "journal",
			retroDir: "retrospectives",
		};
		const merged = Object.assign({}, DEFAULT_SETTINGS, stored);
		expect(merged.ignoredHeadings).toBe("");
		expect(merged.metricTemplates).toBe(DEFAULT_METRIC_TEMPLATES);
		expect(merged.canonicalTags).toBe("");
		expect(merged.providerId).toBe("123");
	});

	it("has empty defaults for ignoredHeadings and canonicalTags", () => {
		expect(DEFAULT_SETTINGS.ignoredHeadings).toBe("");
		expect(DEFAULT_SETTINGS.canonicalTags).toBe("");
	});
});

describe("getProviderOptions", () => {
	it("formats providers with name and type", () => {
		const providers = [
			{
				id: "prov-1",
				name: "LM Studio (Bonsai)",
				type: "lmstudio",
				model: "bonsai-27b",
			},
			{
				id: "prov-2",
				name: "OpenRouter",
				type: "openrouter",
				model: "meta/llama-3",
			},
		];
		expect(getProviderOptions(providers)).toEqual({
			"prov-1": "LM Studio (Bonsai) (lmstudio)",
			"prov-2": "OpenRouter (openrouter)",
		});
	});

	it("falls back to id if name is missing", () => {
		const providers = [{ id: "prov-bare", model: "m" }];
		expect(getProviderOptions(providers)).toEqual({
			"prov-bare": "prov-bare",
		});
	});
});

describe("getModelOptions", () => {
	it("returns hasChoices: false when provider is undefined or has no models", () => {
		expect(getModelOptions(undefined)).toEqual({
			hasChoices: false,
			options: {},
		});
		expect(getModelOptions({ id: "p", model: "" })).toEqual({
			hasChoices: false,
			options: {},
		});
	});

	it("includes default option and sorted availableModels", () => {
		const provider = {
			id: "p1",
			name: "Test",
			model: "default-model",
			availableModels: ["model-b", "model-a", "default-model"],
		};
		const result = getModelOptions(provider);
		expect(result.hasChoices).toBe(true);
		expect(result.options).toEqual({
			"": "Default (default-model)",
			"default-model": "default-model",
			"model-a": "model-a",
			"model-b": "model-b",
		});
	});

	it("preserves currentModel if not already in availableModels", () => {
		const provider = {
			id: "p1",
			model: "m1",
			availableModels: ["m1", "m2"],
		};
		const result = getModelOptions(provider, "custom-saved-model");
		expect(result.hasChoices).toBe(true);
		expect(result.options["custom-saved-model"]).toBe("custom-saved-model");
	});
});
