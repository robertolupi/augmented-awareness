import { describe, it, expect } from "vitest";
import { findSectionEvents, parseEventLine } from "../src/core/events";

describe("parseEventLine", () => {
	it("parses a closed event", () => {
		const ev = parseEventLine("08:30 - 09:30 #work some text");
		expect(ev).not.toBeNull();
		expect(ev!.startMin).toBe(8 * 60 + 30);
		expect(ev!.endMin).toBe(9 * 60 + 30);
		expect(ev!.durationMin).toBe(60);
		expect(ev!.text).toBe("#work some text");
		expect(ev!.tags).toEqual(["work"]);
	});

	it("parses an event without spaces around the dash", () => {
		const ev = parseEventLine("08:30-09:30 #work");
		expect(ev).not.toBeNull();
		expect(ev!.durationMin).toBe(60);
	});

	it("parses an open event with zero duration", () => {
		const ev = parseEventLine("06:04 woke up");
		expect(ev).not.toBeNull();
		expect(ev!.startMin).toBe(6 * 60 + 4);
		expect(ev!.endMin).toBeNull();
		expect(ev!.durationMin).toBe(0);
		expect(ev!.tags).toEqual([]);
	});

	it("wraps overnight events across midnight", () => {
		const ev = parseEventLine("23:00 - 01:00 #sleep");
		expect(ev).not.toBeNull();
		expect(ev!.durationMin).toBe(120);
	});

	it("extracts hierarchical tags", () => {
		const ev = parseEventLine("10:00 - 11:00 #create/write/blog drafting");
		expect(ev).not.toBeNull();
		expect(ev!.tags).toEqual(["create/write/blog"]);
	});

	it("extracts multiple tags anywhere in the text", () => {
		const ev = parseEventLine("10:00 meeting #work with #team/bob");
		expect(ev).not.toBeNull();
		expect(ev!.tags).toEqual(["work", "team/bob"]);
	});

	it("rejects non-event lines", () => {
		expect(parseEventLine("# heading")).toBeNull();
		expect(parseEventLine("some prose")).toBeNull();
		expect(parseEventLine("- [ ] 09:00 task")).toBeNull();
		expect(parseEventLine("")).toBeNull();
		expect(parseEventLine(" 09:00 indented")).toBeNull();
	});

	it("rejects invalid times", () => {
		expect(parseEventLine("25:00 - 26:00 nope")).toBeNull();
		expect(parseEventLine("10:70 nope")).toBeNull();
	});
});

describe("findSectionEvents", () => {
	const page = [
		"# 2025-04-01",
		"",
		"## Journal and events",
		"",
		"06:04 woke up",
		"07:00 #aww did some personal development",
		"08:30-09:30 #work",
		"",
		"## Tasks",
		"",
		"10:00 - 11:00 #not-in-section",
	].join("\n");

	it("collects events only from the named section", () => {
		const events = findSectionEvents(page, "Journal and events");
		expect(events).toHaveLength(3);
		expect(events.map((e) => e.startMin)).toEqual([
			6 * 60 + 4,
			7 * 60,
			8 * 60 + 30,
		]);
	});

	it("returns an empty list when the section is missing", () => {
		expect(findSectionEvents(page, "Schedule")).toEqual([]);
	});

	it("returns an empty list for an empty section name", () => {
		expect(findSectionEvents(page, "  ")).toEqual([]);
	});

	it("ends the section at a deeper-level heading (Go behavior)", () => {
		const nested = [
			"## Schedule",
			"08:00 - 09:00 #a",
			"### Details",
			"10:00 - 11:00 #b",
		].join("\n");
		const events = findSectionEvents(nested, "Schedule");
		expect(events).toHaveLength(1);
		expect(events[0].tags).toEqual(["a"]);
	});

	it("matches the section heading at any level", () => {
		const content = "# Schedule\n08:00 - 09:00 #a\n";
		expect(findSectionEvents(content, "Schedule")).toHaveLength(1);
	});

	it("trims the heading text before matching", () => {
		const content = "##   Schedule   \n08:00 - 09:00 #a\n";
		expect(findSectionEvents(content, "Schedule")).toHaveLength(1);
	});

	it("ignores frontmatter", () => {
		const content = [
			"---",
			"stress: 3",
			"---",
			"## Schedule",
			"08:00 - 09:00 #a",
		].join("\n");
		const events = findSectionEvents(content, "Schedule");
		expect(events).toHaveLength(1);
		expect(events[0].line).toBe(4);
	});

	it("skips non-event lines inside the section", () => {
		const content = [
			"## Schedule",
			"some prose",
			"08:00 - 09:00 #a",
			"- [ ] a task",
		].join("\n");
		expect(findSectionEvents(content, "Schedule")).toHaveLength(1);
	});
});
