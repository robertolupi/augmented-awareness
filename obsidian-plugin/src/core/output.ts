/**
 * Output post-processing, ported from aww/retro_gen.py prepare_output() and
 * MARKDOWN_RE.
 */

// Exact port of MARKDOWN_RE used with re.match(): anchored at the start of
// the (stripped) output; the fence does not need to reach the end.
const MARKDOWN_RE = /^```markdown\n(.*?)\n```/s;

// Strips model internal reasoning wrappers such as <think>...</think>
// or <thought>...</thought> emitted by reasoning models (e.g. DeepSeek, Qwen).
const THINK_RE = /<(?:think|thought)\b[^>]*>[\s\S]*?<\/(?:think|thought)>/gi;

/**
 * Strip reasoning wrappers (<think>...</think>), an enclosing ```markdown fence
 * when the output starts with one (matching MARKDOWN_RE.match semantics),
 * turn ![[ embeds into [[ links, and prepend `# <target page name>` followed by
 * a blank line.
 */
export function prepareOutput(output: string, targetPageName: string): string {
	let out = output.replace(THINK_RE, "").trim();
	const m = MARKDOWN_RE.exec(out);
	if (m) {
		out = m[1];
	}
	out = out.replace(THINK_RE, "").trim();
	out = out.replace(/!\[\[/g, "[[");
	return `# ${targetPageName}\n\n${out}`;
}
