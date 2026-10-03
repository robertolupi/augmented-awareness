/**
 * System prompt generation for Augmented Awareness chat assistant.
 */
import { App, TFile, moment } from "obsidian";
import { getDatetimeContext } from "../tools/datetime";

export interface SystemPromptOptions {
	contextNote?: {
		path: string;
		basename: string;
		content: string;
	} | null;
}

export async function buildChatSystemPrompt(
	app: App,
	options: SystemPromptOptions = {}
): Promise<string> {
	const now = moment();
	const sections: string[] = [
		"You are Augmented Awareness (aww), a thoughtful, intelligent assistant guiding the user to live a more wholesome and reflective life.",
		"You have direct access to the user's Obsidian vault, journal, retrospectives, tasks, and notes via specialized tools. Proactively use these tools to inspect their situation, search for context, check past patterns, and give precise, grounded answers.",
		"",
		"Tool Guidelines:",
		"- Use `search_vault` to find notes across the entire vault when looking for topics, projects, or recurring concepts.",
		"- Use `read_pages` to read specific notes or [[wikilinks]] mentioned in the vault.",
		"- Use `read_journal` to review the past 7 days of daily entries and retrospectives.",
		"- Use `read_tasks` to inspect tasks across any date range (both open and completed).",
		"- Use `read_retro` to check today's retrospectives across all periodic levels.",
		"- Use `list_dates` or `extract_metric` to analyze trends across months.",
		"- Use `calculator` for safe math and date calculations (days between dates, date additions, day of week).",
		"",
		`Current Date and Time:\n${getDatetimeContext(now)}`,
	];

	// Check for aww-scratchpad note in vault
	const scratchpadFile =
		app.metadataCache.getFirstLinkpathDest("aww-scratchpad", "") ||
		app.vault
			.getMarkdownFiles()
			.find((f) => f.basename === "aww-scratchpad");

	if (scratchpadFile && scratchpadFile instanceof TFile) {
		try {
			const scratchContent = await app.vault.cachedRead(scratchpadFile);
			if (scratchContent.trim()) {
				sections.push(
					`\nContextual Memory from [[aww-scratchpad]]:\n${scratchContent.trim()}`
				);
			}
		} catch {
			// Ignore read error
		}
	}

	// Active note context
	if (options.contextNote) {
		sections.push(
			`\nActive Note Context:\nThe user is currently viewing the note [[${options.contextNote.basename}]] (\`${options.contextNote.path}\`):\n${options.contextNote.content}`
		);
	}

	return sections.join("\n\n");
}
