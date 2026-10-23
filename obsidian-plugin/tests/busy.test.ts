import { describe, it, expect, vi } from "vitest";
import { TFile, moment } from "obsidian";
import {
	BusyReport,
	TimeHistogram,
	buildBusyReport,
	formatDurationMin,
} from "../src/core/busy";

function createMockFile(path: string, basename: string): TFile {
	const f = new (TFile as any)();
	f.path = path;
	f.basename = basename;
	return f;
}

describe("TimeHistogram", () => {
	it("creates 48 buckets for 30-minute buckets", () => {
		const h = new TimeHistogram(30);
		expect(h.buckets).toHaveLength(48);
		expect(h.durationMin).toBe(0);
	});

	it("rejects bucket sizes that do not divide 24h", () => {
		expect(() => new TimeHistogram(7 * 60)).toThrow();
		expect(() => new TimeHistogram(50)).toThrow();
	});

	it("adds one hour at the start of the day (hourly buckets)", () => {
		const h = new TimeHistogram(60);
		h.add(0, 60);
		const expected = new Array(24).fill(0);
		expected[0] = 1;
		expect(h.buckets).toEqual(expected);
		expect(h.durationMin).toBe(60);
	});

	it("spans buckets with ceil semantics", () => {
		const h = new TimeHistogram(60);
		h.add(90, 120); // 01:30 + 2h touches buckets 1 and 2
		expect(h.buckets[1]).toBe(1);
		expect(h.buckets[2]).toBe(1);
		expect(h.buckets[3]).toBe(0);
	});

	it("wraps around midnight", () => {
		const h = new TimeHistogram(60);
		h.add(23 * 60, 120);
		expect(h.buckets[23]).toBe(1);
		expect(h.buckets[0]).toBe(1);
	});

	it("ignores zero-duration events", () => {
		const h = new TimeHistogram(60);
		h.add(10 * 60, 0);
		expect(h.buckets.every((b) => b === 0)).toBe(true);
		expect(h.durationMin).toBe(0);
	});

	it("wraps multi-day durations over all buckets", () => {
		const h = new TimeHistogram(60);
		h.add(10 * 60, 48 * 60);
		expect(h.buckets.every((b) => b === 2)).toBe(true);
	});

	it("copies and merges", () => {
		const h1 = new TimeHistogram(60);
		h1.add(0, 60);
		const h2 = h1.copy();
		expect(h2.buckets[0]).toBe(1);
		expect(h2.durationMin).toBe(60);
		h2.add(2 * 60, 60);
		expect(h1.buckets[2]).toBe(0);
		h1.merge(h2);
		expect(h1.buckets[0]).toBe(2);
		expect(h1.buckets[2]).toBe(1);
		expect(h1.durationMin).toBe(180);
	});

	it("rejects merging different bucket sizes", () => {
		const h1 = new TimeHistogram(60);
		const h2 = new TimeHistogram(120);
		expect(() => h1.merge(h2)).toThrow();
	});

	it("maxBucket is at least 1", () => {
		expect(new TimeHistogram(30).maxBucket()).toBe(1);
		const h = new TimeHistogram(30);
		h.add(0, 30);
		h.add(0, 30);
		h.add(0, 30);
		expect(h.maxBucket()).toBe(3);
	});
});

describe("BusyReport", () => {
	it("routes untagged events only to noTags", () => {
		const br = new BusyReport(60);
		br.addEvent(10 * 60, 60, []);
		expect(br.noTags.durationMin).toBe(60);
		expect(br.total.durationMin).toBe(0);
		expect(br.tags.size).toBe(0);
	});

	it("routes tagged events to total and every tag", () => {
		const br = new BusyReport(60);
		br.addEvent(10 * 60, 60, ["tag1", "tag2"]);
		expect(br.total.durationMin).toBe(60);
		expect(br.noTags.durationMin).toBe(0);
		expect(br.tags.get("tag1")!.durationMin).toBe(60);
		expect(br.tags.get("tag2")!.durationMin).toBe(60);
		expect(br.tags.get("tag1")!.bucketMinutes).toBe(60);
	});

	it("ignores empty tags like the Go implementation", () => {
		const br = new BusyReport(60);
		br.addEvent(10 * 60, 60, [""]);
		expect(br.total.durationMin).toBe(60);
		expect(br.tags.size).toBe(0);
	});

	it("expands hierarchical tags shared by at least two tags", () => {
		const br = new BusyReport(60);
		br.addEvent(9 * 60, 60, ["a/b/c"]);
		br.addEvent(10 * 60, 60, ["a/b/d"]);
		br.addEvent(11 * 60, 60, ["x/y"]);
		br.expandTags();
		expect(br.tags.has("a/b")).toBe(true);
		expect(br.tags.has("a")).toBe(true);
		expect(br.tags.has("x")).toBe(false);
		expect(br.tags.get("a/b")!.durationMin).toBe(120);
		expect(br.tags.get("a")!.durationMin).toBe(120);
	});

	it("keeps an ancestor that is itself a real tag", () => {
		const br = new BusyReport(60);
		br.addEvent(9 * 60, 60, ["father"]);
		br.addEvent(10 * 60, 60, ["father/son"]);
		br.expandTags();
		expect(br.tags.get("father")!.durationMin).toBe(120);
	});

	it("sorts tags by duration descending with percent of total", () => {
		const br = new BusyReport(60);
		br.addEvent(9 * 60, 60, ["tag1"]);
		br.addEvent(10 * 60, 120, ["tag2"]);
		br.addEvent(12 * 60, 180, ["tag3"]);
		const sorted = br.sortedTags();
		expect(sorted.map((t) => t.tag)).toEqual(["tag3", "tag2", "tag1"]);
		expect(sorted[0].percent).toBeCloseTo(50);
		expect(sorted[2].percent).toBeCloseTo(100 / 6);
	});

	it("reports zero percent when nothing is tagged", () => {
		const br = new BusyReport(60);
		expect(br.sortedTags()).toEqual([]);
	});
});

describe("formatDurationMin", () => {
	it("formats hours and minutes", () => {
		expect(formatDurationMin(210)).toBe("3h 30m");
		expect(formatDurationMin(60)).toBe("1h");
		expect(formatDurationMin(45)).toBe("45m");
		expect(formatDurationMin(0)).toBe("0m");
	});
});

describe("buildBusyReport", () => {
	const contents: Record<string, string> = {
		"journal/2026/10/2026-10-02.md":
			"## Journal and events\n\n08:30-09:30 #work\n",
		"journal/2026/10/2026-10-03.md":
			"## Journal and events\n\n10:00-11:00 #work #deep\n12:00-12:30 lunch\n",
		// A page without the section is skipped silently.
		"journal/2026/10/2026-10-01.md": "# Just a heading\n\nno events\n",
	};

	function createMockApp(): any {
		return {
			vault: {
				getAbstractFileByPath: (path: string) => {
					if (!(path in contents)) {
						return null;
					}
					const base = path.split("/").pop()!.replace(/\.md$/, "");
					return createMockFile(path, base);
				},
				cachedRead: vi.fn(async (file: TFile) => contents[file.path] ?? ""),
			},
		};
	}

	it("aggregates a rolling window ending at the given date", async () => {
		const report = await buildBusyReport(createMockApp(), {
			endDate: moment("2026-10-03", "YYYY-MM-DD"),
			days: 3,
			journalDir: "journal",
			journalSection: "Journal and events",
		});
		expect(report.total.durationMin).toBe(120);
		expect(report.noTags.durationMin).toBe(30);
		expect(report.tags.get("work")!.durationMin).toBe(120);
		expect(report.tags.get("deep")!.durationMin).toBe(60);
		const sorted = report.sortedTags();
		expect(sorted[0].tag).toBe("work");
		expect(sorted[0].percent).toBeCloseTo(100);
	});

	it("skips missing journal pages", async () => {
		const report = await buildBusyReport(createMockApp(), {
			endDate: moment("2026-10-02", "YYYY-MM-DD"),
			days: 30,
			journalDir: "journal",
			journalSection: "Journal and events",
		});
		expect(report.total.durationMin).toBe(60);
	});

	it("honors a custom journal dir and section", async () => {
		const app: any = {
			vault: {
				getAbstractFileByPath: (path: string) =>
					path === "diary/2026/10/2026-10-03.md"
						? createMockFile(path, "2026-10-03")
						: null,
				cachedRead: async () =>
					"## Schedule\n\n09:00 - 10:30 #work\n",
			},
		};
		const report = await buildBusyReport(app, {
			endDate: moment("2026-10-03", "YYYY-MM-DD"),
			days: 1,
			journalDir: "diary",
			journalSection: "Schedule",
		});
		expect(report.total.durationMin).toBe(90);
		expect(report.tags.get("work")!.durationMin).toBe(90);
	});
});
