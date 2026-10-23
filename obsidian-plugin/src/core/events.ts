/**
 * Journal time-event parsing, ported from the Go implementation
 * (internal/obsidian/event.go and the section logic of page.go).
 *
 * Event lines look like:
 *   03:00 - 04:00 #tag1 #tag2 Some text
 *   03:00 Some text #tag1
 * and live inside a named heading section of a daily journal page.
 */

export interface JournalEvent {
	/** Zero-based line index within the page content (after frontmatter). */
	line: number;
	/** Minutes since midnight. */
	startMin: number;
	/** Minutes since midnight, or null for an open (ongoing) event. */
	endMin: number | null;
	/** Event duration in minutes; 0 for open events. Overnight events wrap. */
	durationMin: number;
	text: string;
	tags: string[];
}

const EVENT_RE = /^(\d{2}):(\d{2})\s*(-\s*(\d{2}):(\d{2}))?\s*(.*?)$/;
const HEADING_RE = /^(#+)\s+(.*)$/;
const MINUTES_PER_DAY = 24 * 60;

function parseClock(hours: string, minutes: string): number | null {
	const h = Number(hours);
	const m = Number(minutes);
	if (h > 23 || m > 59) {
		return null;
	}
	return h * 60 + m;
}

/**
 * Parse a single line into a time event, or return null when the line is
 * not an event. Mirrors MaybeParseEvent in internal/obsidian/event.go.
 */
export function parseEventLine(
	line: string
): Omit<JournalEvent, "line"> | null {
	const match = EVENT_RE.exec(line);
	if (!match) {
		return null;
	}

	const startMin = parseClock(match[1], match[2]);
	if (startMin === null) {
		return null;
	}

	let endMin: number | null = null;
	if (match[4] !== undefined) {
		endMin = parseClock(match[4], match[5]);
		if (endMin === null) {
			return null;
		}
	}

	let durationMin = 0;
	if (endMin !== null) {
		durationMin = endMin - startMin;
		if (durationMin < 0) {
			// an overnight event
			durationMin += MINUTES_PER_DAY;
		}
	}

	const text = match[6].trim();
	const tags = text
		.split(/\s+/)
		.filter((field) => field.startsWith("#"))
		.map((field) => field.slice(1));

	return { startMin, endMin, durationMin, text, tags };
}

/**
 * Extract the time events from the named heading section of a markdown page.
 * The section starts at a heading whose trimmed text matches sectionName
 * exactly (any level) and ends at the next heading of any level, or at the
 * end of the file. Mirrors Page.FindSection + Section.Events in
 * internal/obsidian/page.go (note: the Go code ends the section at any
 * subsequent heading, not only same-or-higher levels).
 */
export function findSectionEvents(
	content: string,
	sectionName: string
): JournalEvent[] {
	const section = sectionName.trim();
	if (!section) {
		return [];
	}

	const lines = content.split("\n");

	// Skip a leading frontmatter block, as the Go Page parser strips it.
	let firstLine = 0;
	if (lines[0]?.trim() === "---") {
		for (let i = 1; i < lines.length; i++) {
			if (lines[i].trim() === "---") {
				firstLine = i + 1;
				break;
			}
		}
	}

	const events: JournalEvent[] = [];
	let inSection = false;
	for (let i = firstLine; i < lines.length; i++) {
		const line = lines[i];
		const heading = HEADING_RE.exec(line);
		if (heading) {
			if (inSection) {
				break;
			}
			if (heading[2].trim() === section) {
				inSection = true;
			}
			continue;
		}
		if (!inSection) {
			continue;
		}
		const parsed = parseEventLine(line);
		if (parsed) {
			events.push({ line: i, ...parsed });
		}
	}
	return events;
}
