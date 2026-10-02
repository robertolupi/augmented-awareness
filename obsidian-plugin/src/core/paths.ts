/**
 * Pure path helpers for journal and retrospective notes.
 * No Obsidian imports: this module is unit-testable under vitest.
 *
 * Path conventions (see doc/obsidian-plugin-design.md):
 *   journal note:        <journalDir>/<yyyy>/<mm>/<yyyy-mm-dd>.md
 *   daily retrospective: <retroDir>/<yyyy>/<mm>/r<yyyy-mm-dd>.md
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
	const escapedDir = journalDir.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	const re = new RegExp(
		`^${escapedDir}/(\\d{4})/(\\d{2})/(\\d{4}-\\d{2}-\\d{2})\\.md$`
	);
	const match = re.exec(path);
	if (!match) {
		return null;
	}
	const [, year, month, date] = match;
	if (date !== `${year}-${month}-${date.slice(8)}`) {
		return null;
	}
	// Strict calendar validation (rejects e.g. 2025-02-30, month 13).
	const [y, m, d] = date.split("-").map(Number);
	if (m < 1 || m > 12 || d < 1 || d > 31) {
		return null;
	}
	const parsed = new Date(Date.UTC(y, m - 1, d));
	if (
		parsed.getUTCFullYear() !== y ||
		parsed.getUTCMonth() !== m - 1 ||
		parsed.getUTCDate() !== d
	) {
		return null;
	}
	return date;
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
