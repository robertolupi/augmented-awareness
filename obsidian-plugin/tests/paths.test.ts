import { describe, expect, it } from "vitest";
import {
	dailyJournalPath,
	dailyRetroPath,
	parseDailyJournalPath,
} from "../src/core/paths";

describe("dailyRetroPath", () => {
	it("maps a daily date to the retrospective path", () => {
		expect(dailyRetroPath("2025-01-02")).toBe(
			"retrospectives/2025/01/r2025-01-02.md"
		);
	});

	it("supports leap day", () => {
		expect(dailyRetroPath("2024-02-29")).toBe(
			"retrospectives/2024/02/r2024-02-29.md"
		);
	});

	it("handles year boundary", () => {
		expect(dailyRetroPath("2025-12-31")).toBe(
			"retrospectives/2025/12/r2025-12-31.md"
		);
		expect(dailyRetroPath("2026-01-01")).toBe(
			"retrospectives/2026/01/r2026-01-01.md"
		);
	});

	it("honours custom directories", () => {
		expect(dailyRetroPath("2025-06-15", "diario", "retro")).toBe(
			"retro/2025/06/r2025-06-15.md"
		);
	});

	it("rejects malformed dates", () => {
		expect(() => dailyRetroPath("2025-1-2")).toThrow();
		expect(() => dailyRetroPath("not-a-date")).toThrow();
	});
});

describe("dailyJournalPath", () => {
	it("maps a daily date to the journal path", () => {
		expect(dailyJournalPath("2025-01-08")).toBe(
			"journal/2025/01/2025-01-08.md"
		);
	});

	it("supports leap day", () => {
		expect(dailyJournalPath("2024-02-29")).toBe(
			"journal/2024/02/2024-02-29.md"
		);
	});

	it("handles year boundary", () => {
		expect(dailyJournalPath("2025-12-31")).toBe(
			"journal/2025/12/2025-12-31.md"
		);
		expect(dailyJournalPath("2026-01-01")).toBe(
			"journal/2026/01/2026-01-01.md"
		);
	});

	it("honours custom journal directory", () => {
		expect(dailyJournalPath("2025-06-15", "diario")).toBe(
			"diario/2025/06/2025-06-15.md"
		);
	});

	it("round-trips through parseDailyJournalPath", () => {
		const date = "2025-01-08";
		const path = dailyJournalPath(date);
		expect(parseDailyJournalPath(path)).toBe(date);
	});

	it("rejects malformed dates", () => {
		expect(() => dailyJournalPath("2025-1-2")).toThrow();
		expect(() => dailyJournalPath("not-a-date")).toThrow();
	});
});

describe("parseDailyJournalPath", () => {
	it("parses a canonical daily journal path", () => {
		expect(parseDailyJournalPath("journal/2025/01/2025-01-02.md")).toBe(
			"2025-01-02"
		);
	});

	it("parses a leap day", () => {
		expect(parseDailyJournalPath("journal/2024/02/2024-02-29.md")).toBe(
			"2024-02-29"
		);
	});

	it("parses year boundary dates", () => {
		expect(parseDailyJournalPath("journal/2025/12/2025-12-31.md")).toBe(
			"2025-12-31"
		);
		expect(parseDailyJournalPath("journal/2026/01/2026-01-01.md")).toBe(
			"2026-01-01"
		);
	});

	it("honours a custom journal directory", () => {
		expect(
			parseDailyJournalPath("diario/2025/06/2025-06-15.md", "diario")
		).toBe("2025-06-15");
	});

	it("returns null for the wrong prefix", () => {
		expect(
			parseDailyJournalPath("retrospectives/2025/01/2025-01-02.md")
		).toBeNull();
		expect(
			parseDailyJournalPath("journal/2025/01/2025-01-02.md", "diario")
		).toBeNull();
	});

	it("returns null for non-date filenames", () => {
		expect(parseDailyJournalPath("journal/2025/01/Y2025.md")).toBeNull();
		expect(
			parseDailyJournalPath("journal/2025/01/r2025-01-02.md")
		).toBeNull();
		expect(
			parseDailyJournalPath("journal/2025/01/2025-01.md")
		).toBeNull();
	});

	it("returns null for nested or extra path segments", () => {
		expect(
			parseDailyJournalPath("journal/2025/01/extra/2025-01-02.md")
		).toBeNull();
		expect(
			parseDailyJournalPath("journal/2025/2025-01-02.md")
		).toBeNull();
		expect(
			parseDailyJournalPath("vault/journal/2025/01/2025-01-02.md")
		).toBeNull();
	});

	it("returns null for invalid calendar dates", () => {
		expect(
			parseDailyJournalPath("journal/2023/02/2023-02-29.md")
		).toBeNull();
		expect(
			parseDailyJournalPath("journal/2025/13/2025-13-01.md")
		).toBeNull();
		expect(
			parseDailyJournalPath("journal/2025/00/2025-00-10.md")
		).toBeNull();
	});

	it("returns null when filename date mismatches directory components", () => {
		expect(
			parseDailyJournalPath("journal/2025/01/2025-02-02.md")
		).toBeNull();
	});
});
