import { describe, expect, it } from "vitest";
import { moment } from "obsidian";
import {
	formatPeriod,
	isDailyString,
	isMonthlyString,
	isWeeklyString,
	isYearlyString,
	parsePeriodString,
	wholeMonth,
	wholeWeek,
	wholeYear,
} from "../src/core/calendar";

describe("Period string regex validators", () => {
	it("recognizes daily strings", () => {
		expect(isDailyString("2025-01-08")).toBe(true);
		expect(isDailyString("2025-1-8")).toBe(false);
		expect(isDailyString("2025-01")).toBe(false);
		expect(isDailyString("2025-W02")).toBe(false);
	});

	it("recognizes weekly strings", () => {
		expect(isWeeklyString("2025-W02")).toBe(true);
		expect(isWeeklyString("2025-W53")).toBe(true);
		expect(isWeeklyString("2025-02")).toBe(false);
		expect(isWeeklyString("2025-W2")).toBe(false);
	});

	it("recognizes monthly strings", () => {
		expect(isMonthlyString("2025-01")).toBe(true);
		expect(isMonthlyString("2025-12")).toBe(true);
		expect(isMonthlyString("2025-01-08")).toBe(false);
		expect(isMonthlyString("2025")).toBe(false);
	});

	it("recognizes yearly strings", () => {
		expect(isYearlyString("2025")).toBe(true);
		expect(isYearlyString("Y2025")).toBe(true);
		expect(isYearlyString("2025-01")).toBe(false);
	});
});

describe("formatPeriod", () => {
	it("formats daily", () => {
		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		expect(formatPeriod(m, "daily")).toBe("2025-01-08");
	});

	it("formats weekly using ISO week-year", () => {
		// 2025-01-08 is Wednesday of week 2
		const m1 = moment("2025-01-08", "YYYY-MM-DD", true);
		expect(formatPeriod(m1, "weekly")).toBe("2025-W02");

		// 2024-12-30 is Monday of ISO week 1 of 2025
		const m2 = moment("2024-12-30", "YYYY-MM-DD", true);
		expect(formatPeriod(m2, "weekly")).toBe("2025-W01");

		// 2021-01-01 is Friday of ISO week 53 of 2020
		const m3 = moment("2021-01-01", "YYYY-MM-DD", true);
		expect(formatPeriod(m3, "weekly")).toBe("2020-W53");
	});

	it("formats monthly", () => {
		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		expect(formatPeriod(m, "monthly")).toBe("2025-01");
	});

	it("formats yearly", () => {
		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		expect(formatPeriod(m, "yearly")).toBe("2025");
	});
});

describe("parsePeriodString", () => {
	it("parses daily strings", () => {
		const parsed = parsePeriodString("2025-01-08");
		expect(parsed).not.toBeNull();
		expect(parsed?.level).toBe("daily");
		expect(parsed?.date.format("YYYY-MM-DD")).toBe("2025-01-08");
	});

	it("parses weekly strings", () => {
		const parsed = parsePeriodString("2025-W02");
		expect(parsed).not.toBeNull();
		expect(parsed?.level).toBe("weekly");
		expect(parsed?.date.isoWeekYear()).toBe(2025);
		expect(parsed?.date.isoWeek()).toBe(2);
	});

	it("parses monthly strings", () => {
		const parsed = parsePeriodString("2025-01");
		expect(parsed).not.toBeNull();
		expect(parsed?.level).toBe("monthly");
		expect(parsed?.date.format("YYYY-MM")).toBe("2025-01");
	});

	it("parses yearly strings", () => {
		const parsed1 = parsePeriodString("Y2025");
		expect(parsed1).not.toBeNull();
		expect(parsed1?.level).toBe("yearly");
		expect(parsed1?.date.format("YYYY")).toBe("2025");

		const parsed2 = parsePeriodString("2025");
		expect(parsed2).not.toBeNull();
		expect(parsed2?.level).toBe("yearly");
		expect(parsed2?.date.format("YYYY")).toBe("2025");
	});

	it("returns null on invalid strings", () => {
		expect(parsePeriodString("random-note")).toBeNull();
		expect(parsePeriodString("2025-99-99")).toBeNull();
	});
});

describe("wholeWeek", () => {
	it("returns 7 dates Monday to Sunday", () => {
		const days = wholeWeek("2025-01-08");
		expect(days).toEqual([
			"2025-01-06",
			"2025-01-07",
			"2025-01-08",
			"2025-01-09",
			"2025-01-10",
			"2025-01-11",
			"2025-01-12",
		]);
	});

	it("handles week crossing year boundary", () => {
		// 2024-12-31 is Tuesday
		const days = wholeWeek("2024-12-31");
		expect(days).toEqual([
			"2024-12-30",
			"2024-12-31",
			"2025-01-01",
			"2025-01-02",
			"2025-01-03",
			"2025-01-04",
			"2025-01-05",
		]);
	});
});

describe("wholeMonth", () => {
	it("returns 31 days for January 2025", () => {
		const days = wholeMonth("2025-01-15");
		expect(days).toHaveLength(31);
		expect(days[0]).toBe("2025-01-01");
		expect(days[30]).toBe("2025-01-31");
	});

	it("handles leap year February 2024 (29 days)", () => {
		const days = wholeMonth("2024-02-10");
		expect(days).toHaveLength(29);
		expect(days[0]).toBe("2024-02-01");
		expect(days[28]).toBe("2024-02-29");
	});

	it("handles non-leap year February 2025 (28 days)", () => {
		const days = wholeMonth("2025-02-10");
		expect(days).toHaveLength(28);
		expect(days[0]).toBe("2025-02-01");
		expect(days[27]).toBe("2025-02-28");
	});
});

describe("wholeYear", () => {
	it("returns 366 days for leap year 2024", () => {
		const days = wholeYear("2024-06-01");
		expect(days).toHaveLength(366);
		expect(days[0]).toBe("2024-01-01");
		expect(days[365]).toBe("2024-12-31");
		expect(days).toContain("2024-02-29");
	});

	it("returns 365 days for non-leap year 2025", () => {
		const days = wholeYear("2025-01-01");
		expect(days).toHaveLength(365);
		expect(days[0]).toBe("2025-01-01");
		expect(days[364]).toBe("2025-12-31");
		expect(days).not.toContain("2025-02-29");
	});
});
