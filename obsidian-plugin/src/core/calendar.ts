import { moment } from "obsidian";

export type Level = "daily" | "weekly" | "monthly" | "yearly";

export const ALL_LEVELS: Level[] = ["daily", "weekly", "monthly", "yearly"];

/**
 * Return true if str is YYYY-MM-DD.
 */
export function isDailyString(str: string): boolean {
	return /^\d{4}-\d{2}-\d{2}$/.test(str);
}

/**
 * Return true if str is YYYY-Www.
 */
export function isWeeklyString(str: string): boolean {
	return /^\d{4}-W\d{2}$/.test(str);
}

/**
 * Return true if str is YYYY-MM.
 */
export function isMonthlyString(str: string): boolean {
	return /^\d{4}-\d{2}$/.test(str);
}

/**
 * Return true if str is YYYY or YYYYY.
 */
export function isYearlyString(str: string): boolean {
	return /^(?:Y\d{4}|\d{4})$/.test(str);
}

/**
 * Format a moment into the canonical identifier for a level.
 * - daily: YYYY-MM-DD
 * - weekly: YYYY-Www (using isoWeekYear)
 * - monthly: YYYY-MM
 * - yearly: YYYY
 */
export function formatPeriod(date: moment.Moment, level: Level): string {
	switch (level) {
		case "daily":
			return date.format("YYYY-MM-DD");
		case "weekly": {
			const isoYear = date.isoWeekYear();
			const week = String(date.isoWeek()).padStart(2, "0");
			return `${isoYear}-W${week}`;
		}
		case "monthly":
			return date.format("YYYY-MM");
		case "yearly":
			return date.format("YYYY");
	}
}

/**
 * Parse a period string (e.g. 2025-01-08, 2025-W02, 2025-01, Y2025, 2025)
 * into a reference moment and its level.
 */
export function parsePeriodString(
	str: string
): { date: moment.Moment; level: Level } | null {
	const trimmed = str.trim();
	if (isDailyString(trimmed)) {
		const m = moment(trimmed, "YYYY-MM-DD", true);
		return m.isValid() ? { date: m, level: "daily" } : null;
	}
	if (isWeeklyString(trimmed)) {
		const m = moment(trimmed, "GGGG-[W]WW", true);
		return m.isValid() ? { date: m, level: "weekly" } : null;
	}
	if (isMonthlyString(trimmed)) {
		const m = moment(trimmed, "YYYY-MM", true);
		return m.isValid() ? { date: m, level: "monthly" } : null;
	}
	if (isYearlyString(trimmed)) {
		const yearStr = trimmed.startsWith("Y") ? trimmed.slice(1) : trimmed;
		const m = moment(yearStr, "YYYY", true);
		return m.isValid() ? { date: m, level: "yearly" } : null;
	}
	return null;
}

/**
 * Return the 7 daily dates (Monday to Sunday) for the ISO week containing the date.
 * Returns ISO strings: YYYY-MM-DD.
 */
export function wholeWeek(date: moment.Moment | string): string[] {
	const m = typeof date === "string" ? moment(date, "YYYY-MM-DD", true) : date.clone();
	if (!m.isValid()) {
		throw new Error(`Invalid date for wholeWeek: ${date}`);
	}
	const monday = m.clone().startOf("isoWeek");
	const result: string[] = [];
	for (let i = 0; i < 7; i++) {
		result.push(monday.clone().add(i, "days").format("YYYY-MM-DD"));
	}
	return result;
}

/**
 * Return all dates (YYYY-MM-DD) for each day of the month containing the date.
 */
export function wholeMonth(date: moment.Moment | string): string[] {
	const m =
		typeof date === "string"
			? moment(date, ["YYYY-MM-DD", "YYYY-MM"], true)
			: date.clone();
	if (!m.isValid()) {
		throw new Error(`Invalid date for wholeMonth: ${date}`);
	}
	const start = m.clone().startOf("month");
	const daysInMonth = start.daysInMonth();
	const result: string[] = [];
	for (let i = 0; i < daysInMonth; i++) {
		result.push(start.clone().add(i, "days").format("YYYY-MM-DD"));
	}
	return result;
}

/**
 * Return all dates (YYYY-MM-DD) for each day of the calendar year containing the date.
 */
export function wholeYear(date: moment.Moment | string): string[] {
	const m =
		typeof date === "string"
			? moment(date, ["YYYY-MM-DD", "YYYY", "YYYY-MM", "Y-YYYY"], true)
			: date.clone();
	if (!m.isValid()) {
		throw new Error(`Invalid date for wholeYear: ${date}`);
	}
	const start = m.clone().startOf("year");
	const end = m.clone().endOf("year");
	const result: string[] = [];
	const curr = start.clone();
	while (curr.isSameOrBefore(end, "day")) {
		result.push(curr.format("YYYY-MM-DD"));
		curr.add(1, "days");
	}
	return result;
}
