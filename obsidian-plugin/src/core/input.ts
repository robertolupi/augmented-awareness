/**
 * Pure daily-input preparation, ported from aww/obsidian.py (Page.content,
 * strip_sections, FRONTMATTER_RE, CODEBLOCKS_RE) and aww/retro_gen.py
 * (page_content, METRIC_FORMATTERS). No Obsidian imports.
 */

// Exact ports of the Python regexes (re.DOTALL | re.MULTILINE).
// FRONTMATTER_RE is used with .sub() in Python, so ^ is anchored at any
// line start (MULTILINE), not only at the start of the file.
const FRONTMATTER_RE = /^---\n(.*?)\n---\n/gms;
// Anchored at the start of the string, like Python's FRONTMATTER_RE.match().
const FRONTMATTER_MATCH_RE = /^---\n(.*?)\n---\n/s;
// Requires a preceding newline (consumed on removal) and a lowercase-only
// language tag; the closing fence must be followed by a newline.
const CODEBLOCKS_RE = /\n```([a-z]+)\n(.*?)\n```\n/gs;
const HEADER_RE = /^(#+)\s+(.*?)\s*$/;

export function stripFrontmatter(text: string): string {
	return text.replace(FRONTMATTER_RE, "");
}

export function stripCodeBlocks(text: string): string {
	return text.replace(CODEBLOCKS_RE, "");
}

/**
 * Remove all sections whose header title matches any of the given headers
 * (case-insensitive). A removed section includes its subsections, up to the
 * next header of the same or higher level. Port of strip_sections().
 */
export function stripSections(text: string, headers: string[]): string {
	const ignored = new Set(
		headers.map((h) => h.trim().toLowerCase()).filter((h) => h.length > 0)
	);
	if (ignored.size === 0) {
		return text;
	}
	const out: string[] = [];
	let skipLevel: number | null = null;
	// Split into lines keeping their terminators, like splitlines(keepends=True)
	// for \n / \r\n / \r endings.
	const lines = text.match(/[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+$/g) ?? [];
	for (const line of lines) {
		const m = HEADER_RE.exec(line.replace(/[\r\n]+$/, ""));
		if (m) {
			const level = m[1].length;
			if (skipLevel !== null && level > skipLevel) {
				continue; // still inside an ignored section
			}
			skipLevel = ignored.has(m[2].trim().toLowerCase()) ? level : null;
			if (skipLevel !== null) {
				continue;
			}
		} else if (skipLevel !== null) {
			continue;
		}
		out.push(line);
	}
	return out.join("");
}

export type FrontmatterValue = string | number | boolean | null;
export type Frontmatter = Record<string, FrontmatterValue>;

/**
 * Parse the YAML frontmatter block at the start of the file into a record of
 * simple scalars. Only top-level `key: value` pairs are supported; nested or
 * list values are skipped. Journal notes only use simple scalars.
 */
export function frontmatterOf(text: string): Frontmatter {
	const m = FRONTMATTER_MATCH_RE.exec(text);
	if (!m) {
		return {};
	}
	const result: Frontmatter = {};
	for (const line of m[1].split("\n")) {
		if (!line || /^\s/.test(line) || line.startsWith("#")) {
			continue; // nested/continuation lines and comments are unsupported
		}
		const kv = /^([^:]+):\s*(.*)$/.exec(line);
		if (!kv) {
			continue;
		}
		const key = kv[1].trim();
		if (!key) {
			continue;
		}
		result[key] = parseScalar(kv[2].trim());
	}
	return result;
}

function parseScalar(raw: string): FrontmatterValue {
	if (raw === "" || raw === "~" || raw === "null" || raw === "Null") {
		return null;
	}
	if (
		(raw.startsWith('"') && raw.endsWith('"') && raw.length >= 2) ||
		(raw.startsWith("'") && raw.endsWith("'") && raw.length >= 2)
	) {
		return raw.slice(1, -1);
	}
	if (raw === "true" || raw === "True") {
		return true;
	}
	if (raw === "false" || raw === "False") {
		return false;
	}
	if (/^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/.test(raw)) {
		return Number(raw);
	}
	return raw;
}

/** Format a scalar the way Python's str() would for str.format(). */
function formatScalar(value: FrontmatterValue): string {
	if (typeof value === "boolean") {
		return value ? "True" : "False";
	}
	return String(value);
}

export interface PrepareInputOptions {
	/** Headings whose sections are removed (applied at the daily level). */
	ignoredHeaders?: string[];
	/** Ordered [frontmatter key, template] pairs; template may contain {}. */
	metrics?: [string, string][];
}

/**
 * Port of retro_gen.page_content() for a daily node: a `Page: [[<name>]]`
 * prefix line, the cleaned content, then one line per metric whose key is
 * present in the frontmatter, in metric-table order.
 */
export function prepareInput(
	pageName: string,
	rawText: string,
	opts: PrepareInputOptions = {}
): string {
	const fm = frontmatterOf(rawText);
	let content = stripFrontmatter(rawText);
	content = stripCodeBlocks(content);
	if (opts.ignoredHeaders && opts.ignoredHeaders.length > 0) {
		content = stripSections(content, opts.ignoredHeaders);
	}
	const parts = [`Page: [[${pageName}]]`, content];
	if (Object.keys(fm).length > 0 && opts.metrics) {
		for (const [key, template] of opts.metrics) {
			const value = fm[key];
			if (value !== undefined && value !== null) {
				parts.push(template.split("{}").join(formatScalar(value)));
			}
		}
	}
	return parts.join("\n");
}
