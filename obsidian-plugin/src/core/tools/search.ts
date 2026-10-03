/**
 * Full-vault search tool leveraging Obsidian's prepareSimpleSearch and cachedRead.
 */
import { App, TFile, prepareSimpleSearch, SearchResult } from "obsidian";

export interface SearchVaultOptions {
	query: string;
	limit?: number; // default 5, max 20
}

export interface SearchMatchItem {
	file: TFile;
	score: number;
	snippet: string;
}

export async function searchVault(
	app: App,
	options: SearchVaultOptions
): Promise<string> {
	const query = options.query?.trim();
	if (!query) {
		return "Error: Empty search query.";
	}

	const limit = Math.min(Math.max(options.limit || 5, 1), 20);
	const searchFn = prepareSimpleSearch(query);
	const files = app.vault.getMarkdownFiles();
	const matches: SearchMatchItem[] = [];

	for (const file of files) {
		const nameMatch = searchFn(file.basename);
		const pathMatch = searchFn(file.path);

		let contentMatch: SearchResult | null = null;
		let content = "";

		try {
			content = await app.vault.cachedRead(file);
			contentMatch = searchFn(content);
		} catch {
			// If file cannot be read, skip content matching
		}

		if (!nameMatch && !pathMatch && !contentMatch) {
			continue;
		}

		// Calculate composite score
		// Give heavy weight to file name matches
		let totalScore = 0;
		if (nameMatch) totalScore += Math.abs(nameMatch.score) + 15;
		if (pathMatch) totalScore += Math.abs(pathMatch.score) + 5;
		if (contentMatch) totalScore += Math.abs(contentMatch.score);

		// Extract best snippet
		let snippet = "";
		if (contentMatch && contentMatch.matches.length > 0) {
			const [start, end] = contentMatch.matches[0];
			snippet = extractSnippet(content, start, end);
		} else if (content) {
			// Name matched, show start of note
			snippet = content.slice(0, 180).trim().replace(/\n+/g, " ");
			if (content.length > 180) snippet += "...";
		}

		matches.push({
			file,
			score: totalScore,
			snippet,
		});
	}

	// Sort descending by score
	matches.sort((a, b) => b.score - a.score);
	const topResults = matches.slice(0, limit);

	if (topResults.length === 0) {
		return `No notes found in the vault matching "${query}".`;
	}

	const lines: string[] = [
		`Found ${topResults.length} matching note(s) for query "${query}":\n`,
	];

	topResults.forEach((item, idx) => {
		const link = `[[${item.file.basename}]]`;
		lines.push(`${idx + 1}. ${link} (\`${item.file.path}\`)`);
		if (item.snippet) {
			lines.push(`   > ${item.snippet}`);
		}
		lines.push("");
	});

	return lines.join("\n").trim();
}

/**
 * Extract snippet around match offset, expanding to sentence / paragraph boundaries.
 */
function extractSnippet(
	text: string,
	startOffset: number,
	endOffset: number,
	contextChars = 100
): string {
	const minIdx = Math.max(0, startOffset - contextChars);
	const maxIdx = Math.min(text.length, endOffset + contextChars);

	let prefix = text.slice(minIdx, startOffset);
	let matched = text.slice(startOffset, endOffset);
	let suffix = text.slice(endOffset, maxIdx);

	// Find preceding newline or sentence boundary
	const lastNewline = prefix.lastIndexOf("\n");
	if (lastNewline !== -1) {
		prefix = prefix.slice(lastNewline + 1);
	} else if (minIdx > 0) {
		prefix = "..." + prefix.trimStart();
	}

	// Find following newline or sentence boundary
	const nextNewline = suffix.indexOf("\n");
	if (nextNewline !== -1) {
		suffix = suffix.slice(0, nextNewline);
	} else if (maxIdx < text.length) {
		suffix = suffix.trimEnd() + "...";
	}

	const snippet = (prefix + "**" + matched + "**" + suffix)
		.replace(/\s+/g, " ")
		.trim();

	return snippet;
}
