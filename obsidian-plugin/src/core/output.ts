/**
 * Output post-processing, ported from aww/retro_gen.py prepare_output() and
 * MARKDOWN_RE.
 */

// Exact port of MARKDOWN_RE used with re.match(): anchored at the start of
// the (stripped) output; the fence does not need to reach the end.
const MARKDOWN_RE = /^```markdown\n(.*?)\n```/s;

/**
 * Strip an enclosing ```markdown fence when the output starts with one
 * (matching MARKDOWN_RE.match semantics), turn ![[ embeds into [[ links,
 * and prepend `# <target page name>` followed by a blank line.
 */
export function prepareOutput(output: string, targetPageName: string): string {
	let out = output.trim();
	const m = MARKDOWN_RE.exec(out);
	if (m) {
		out = m[1];
	}
	out = out.replace(/!\[\[/g, "[[");
	return `# ${targetPageName}\n\n${out}`;
}
