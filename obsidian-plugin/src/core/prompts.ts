import dailyTemplate from "../prompts/daily.md";
import weeklyTemplate from "../prompts/weekly.md";
import monthlyTemplate from "../prompts/monthly.md";
import yearlyTemplate from "../prompts/yearly.md";
import { Level } from "./calendar";

/**
 * Minimal prompt renderer covering exactly what the retrospective prompts
 * use: `{% if <var> %} ... {% else %} ... {% endif %}` and `{{ <var> }}`
 * interpolation. No loops. Mirrors how aww/prompts.py renders the bundled
 * templates with Jinja (default undefined -> empty string, truthiness rules).
 */

const IF_BLOCK_RE =
	/\{%\s*if\s+([A-Za-z_][A-Za-z0-9_]*)\s*%\}([\s\S]*?)(?:\{%\s*else\s*%\}([\s\S]*?))?\{%\s*endif\s*%\}/;
const VAR_RE = /\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}/g;

function isTruthy(value: unknown): boolean {
	if (Array.isArray(value)) {
		return value.length > 0;
	}
	return Boolean(value);
}

export function renderTemplate(
	template: string,
	vars: Record<string, unknown>
): string {
	let out = template;
	let m: RegExpExecArray | null;
	while ((m = IF_BLOCK_RE.exec(out)) !== null) {
		const replacement = isTruthy(vars[m[1]]) ? m[2] : m[3] ?? "";
		out = out.slice(0, m.index) + replacement + out.slice(m.index + m[0].length);
	}
	return out.replace(VAR_RE, (_all, name: string) => {
		const value = vars[name];
		return value === undefined || value === null ? "" : String(value);
	});
}

/**
 * Port of the canonical-tag normalization in RecursiveGenerator.__init__:
 * keys are trimmed, lowercased, spaces become underscores; empty keys are
 * dropped; descriptions are trimmed. Later duplicates overwrite earlier ones.
 */
export function normalizeTags(
	tags: Record<string, string>
): Record<string, string> {
	const normalized: Record<string, string> = {};
	for (const [tag, desc] of Object.entries(tags)) {
		const t = tag.trim().toLowerCase().replace(/ /g, "_");
		if (!t) {
			continue;
		}
		normalized[t] = (desc ?? "").trim();
	}
	return normalized;
}

/** Sorted list of normalized tag names (the `canonical_tags` variable). */
export function canonicalTagNames(tags: Record<string, string>): string[] {
	return Object.keys(normalizeTags(tags)).sort();
}

/**
 * Port of the canonical_tags_block construction: one `- #tag: description`
 * line per normalized tag (or `- #tag` when the description is empty),
 * ordered by normalized tag name.
 */
export function buildTagsBlock(tags: Record<string, string>): string {
	const normalized = normalizeTags(tags);
	return Object.keys(normalized)
		.sort()
		.map((tag) => {
			const desc = normalized[tag];
			return desc ? `- #${tag}: ${desc}` : `- #${tag}`;
		})
		.join("\n");
}

export const PROMPT_TEMPLATES: Record<Level, string> = {
	daily: dailyTemplate,
	weekly: weeklyTemplate,
	monthly: monthlyTemplate,
	yearly: yearlyTemplate,
};

export function renderRetroPrompt(
	level: Level,
	tags: Record<string, string>
): string {
	const template = PROMPT_TEMPLATES[level];
	const canonical_tags = canonicalTagNames(tags);
	const canonical_tags_block = buildTagsBlock(tags);
	return renderTemplate(template, {
		canonical_tags,
		canonical_tags_block,
	});
}
