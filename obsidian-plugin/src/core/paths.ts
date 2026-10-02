import { moment } from "obsidian";
import { Level } from "./calendar";

/**
 * Pure path helpers for journal and retrospective notes.
 *
 * Path conventions (see doc/obsidian-plugin-design.md):
 *   journal note:
 *     daily:   <journalDir>/<yyyy>/<mm>/<yyyy-mm-dd>.md
 *     weekly:  <journalDir>/<iso_year>/weeks/<iso_year>-W<ww>.md
 *     monthly: <journalDir>/<yyyy>/months/<yyyy-mm>.md
 *     yearly:  <journalDir>/<yyyy>/Y<yyyy>.md
 *   retrospective note:
 *     daily:   <retroDir>/<yyyy>/<mm>/r<yyyy-mm-dd>.md
 *     weekly:  <retroDir>/<iso_year>/weeks/r<iso_year>-W<ww>.md
 *     monthly: <retroDir>/<yyyy>/months/r<yyyy-mm>.md
 *     yearly:  <retroDir>/<yyyy>/r<yyyy>.md
 */

const DATE_RE = /^(\d{4})-(\d{2})-(\d{2})$/;

export function dailyRetroPath(
	dateISO: string,
	journalDir = "journal",
	retroDir = "retrospectives"
): string {
	const match = DATE_RE.exec(dateISO);
	if (!match) {
		throw new Error(
			`Invalid ISO date "${dateISO}"; expected yyyy-mm-dd`
		);
	}
	const [, year, month] = match;
	void journalDir; // journal dir does not affect the retrospective path
	return `${retroDir}/${year}/${month}/r${dateISO}.md`;
}

export function dailyJournalPath(
	dateISO: string,
	journalDir = "journal"
): string {
	const match = DATE_RE.exec(dateISO);
	if (!match) {
		throw new Error(
			`Invalid ISO date "${dateISO}"; expected yyyy-mm-dd`
		);
	}
	const [, year, month] = match;
	return `${journalDir}/${year}/${month}/${dateISO}.md`;
}

export function parseDailyJournalPath(
	path: string,
	journalDir = "journal"
): string | null {
	const result = parseJournalPath(path, journalDir);
	if (result && result.level === "daily") {
		return result.date.format("YYYY-MM-DD");
	}
	return null;
}

export function journalPath(
	date: moment.Moment,
	level: Level,
	journalDir = "journal"
): string {
	switch (level) {
		case "daily":
			return `${journalDir}/${date.format("YYYY")}/${date.format("MM")}/${date.format("YYYY-MM-DD")}.md`;
		case "weekly": {
			const isoYear = date.isoWeekYear();
			const week = String(date.isoWeek()).padStart(2, "0");
			return `${journalDir}/${isoYear}/weeks/${isoYear}-W${week}.md`;
		}
		case "monthly":
			return `${journalDir}/${date.format("YYYY")}/months/${date.format("YYYY-MM")}.md`;
		case "yearly":
			return `${journalDir}/${date.format("YYYY")}/Y${date.format("YYYY")}.md`;
	}
}

export function retroPath(
	date: moment.Moment,
	level: Level,
	retroDir = "retrospectives"
): string {
	switch (level) {
		case "daily":
			return `${retroDir}/${date.format("YYYY")}/${date.format("MM")}/r${date.format("YYYY-MM-DD")}.md`;
		case "weekly": {
			const isoYear = date.isoWeekYear();
			const week = String(date.isoWeek()).padStart(2, "0");
			return `${retroDir}/${isoYear}/weeks/r${isoYear}-W${week}.md`;
		}
		case "monthly":
			return `${retroDir}/${date.format("YYYY")}/months/r${date.format("YYYY-MM")}.md`;
		case "yearly":
			return `${retroDir}/${date.format("YYYY")}/r${date.format("YYYY")}.md`;
	}
}

export function parseJournalPath(
	path: string,
	journalDir = "journal"
): { date: moment.Moment; level: Level } | null {
	const escapedDir = journalDir.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

	// 1. Daily: journal/<yyyy>/<mm>/<yyyy-mm-dd>.md
	const dailyMatch = new RegExp(
		`^${escapedDir}/(\\d{4})/(\\d{2})/(\\d{4}-\\d{2}-\\d{2})\\.md$`
	).exec(path);
	if (dailyMatch) {
		const [, year, month, dateStr] = dailyMatch;
		if (dateStr.startsWith(`${year}-${month}-`)) {
			const m = moment(dateStr, "YYYY-MM-DD", true);
			if (m.isValid()) {
				return { date: m, level: "daily" };
			}
		}
		return null;
	}

	// 2. Weekly: journal/<iso_year>/weeks/<iso_year>-W<ww>.md
	const weeklyMatch = new RegExp(
		`^${escapedDir}/(\\d{4})/weeks/(\\d{4}-W\\d{2})\\.md$`
	).exec(path);
	if (weeklyMatch) {
		const [, year, weekStr] = weeklyMatch;
		if (weekStr.startsWith(`${year}-W`)) {
			const m = moment(weekStr, "GGGG-[W]WW", true);
			if (m.isValid()) {
				return { date: m, level: "weekly" };
			}
		}
		return null;
	}

	// 3. Monthly: journal/<yyyy>/months/<yyyy-mm>.md
	const monthlyMatch = new RegExp(
		`^${escapedDir}/(\\d{4})/months/(\\d{4}-\\d{2})\\.md$`
	).exec(path);
	if (monthlyMatch) {
		const [, year, monthStr] = monthlyMatch;
		if (monthStr.startsWith(`${year}-`)) {
			const m = moment(monthStr, "YYYY-MM", true);
			if (m.isValid()) {
				return { date: m, level: "monthly" };
			}
		}
		return null;
	}

	// 4. Yearly: journal/<yyyy>/Y<yyyy>.md
	const yearlyMatch = new RegExp(
		`^${escapedDir}/(\\d{4})/Y(\\d{4})\\.md$`
	).exec(path);
	if (yearlyMatch) {
		const [, year, yearFile] = yearlyMatch;
		if (year === yearFile) {
			const m = moment(year, "YYYY", true);
			if (m.isValid()) {
				return { date: m, level: "yearly" };
			}
		}
		return null;
	}

	return null;
}

export function parseRetroPath(
	path: string,
	retroDir = "retrospectives"
): { date: moment.Moment; level: Level } | null {
	const escapedDir = retroDir.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

	// 1. Daily: retrospectives/<yyyy>/<mm>/r<yyyy-mm-dd>.md
	const dailyMatch = new RegExp(
		`^${escapedDir}/(\\d{4})/(\\d{2})/r(\\d{4}-\\d{2}-\\d{2})\\.md$`
	).exec(path);
	if (dailyMatch) {
		const [, year, month, dateStr] = dailyMatch;
		if (dateStr.startsWith(`${year}-${month}-`)) {
			const m = moment(dateStr, "YYYY-MM-DD", true);
			if (m.isValid()) {
				return { date: m, level: "daily" };
			}
		}
		return null;
	}

	// 2. Weekly: retrospectives/<iso_year>/weeks/r<iso_year>-W<ww>.md
	const weeklyMatch = new RegExp(
		`^${escapedDir}/(\\d{4})/weeks/r(\\d{4}-W\\d{2})\\.md$`
	).exec(path);
	if (weeklyMatch) {
		const [, year, weekStr] = weeklyMatch;
		if (weekStr.startsWith(`${year}-W`)) {
			const m = moment(weekStr, "GGGG-[W]WW", true);
			if (m.isValid()) {
				return { date: m, level: "weekly" };
			}
		}
		return null;
	}

	// 3. Monthly: retrospectives/<yyyy>/months/r<yyyy-mm>.md
	const monthlyMatch = new RegExp(
		`^${escapedDir}/(\\d{4})/months/r(\\d{4}-\\d{2})\\.md$`
	).exec(path);
	if (monthlyMatch) {
		const [, year, monthStr] = monthlyMatch;
		if (monthStr.startsWith(`${year}-`)) {
			const m = moment(monthStr, "YYYY-MM", true);
			if (m.isValid()) {
				return { date: m, level: "monthly" };
			}
		}
		return null;
	}

	// 4. Yearly: retrospectives/<yyyy>/r<yyyy>.md
	const yearlyMatch = new RegExp(
		`^${escapedDir}/(\\d{4})/r(\\d{4})\\.md$`
	).exec(path);
	if (yearlyMatch) {
		const [, year, yearFile] = yearlyMatch;
		if (year === yearFile) {
			const m = moment(year, "YYYY", true);
			if (m.isValid()) {
				return { date: m, level: "yearly" };
			}
		}
		return null;
	}

	return null;
}

export function parseJournalOrRetroPath(
	path: string,
	journalDir = "journal",
	retroDir = "retrospectives"
): { date: moment.Moment; level: Level; isRetro: boolean } | null {
	const j = parseJournalPath(path, journalDir);
	if (j) {
		return { ...j, isRetro: false };
	}
	const r = parseRetroPath(path, retroDir);
	if (r) {
		return { ...r, isRetro: true };
	}
	return null;
}

/**
 * Compute the progressive backup path for an existing file:
 * e.g. path/to/r2025-01-08.md -> path/to/r2025-01-08.1.md
 */
export function progressiveBackupPath(targetPath: string, n: number): string {
	if (n < 1 || !Number.isInteger(n)) {
		throw new Error(
			`Progressive backup number must be a positive integer, got ${n}`
		);
	}
	if (targetPath.endsWith(".md")) {
		return `${targetPath.slice(0, -3)}.${n}.md`;
	}
	return `${targetPath}.${n}`;
}

/**
 * Find the next available backup path using the provided existence check.
 */
export function findNextBackupPath(
	targetPath: string,
	exists: (path: string) => boolean
): string {
	let i = 1;
	while (true) {
		const candidate = progressiveBackupPath(targetPath, i);
		if (!exists(candidate)) {
			return candidate;
		}
		i++;
	}
}
