/**
 * Task extraction tool leveraging Obsidian's MetadataCache.
 */
import { App, TFile, moment } from "obsidian";
import { dailyJournalPath } from "../paths";

export interface ReadTasksOptions {
	start?: string; // YYYY-MM-DD
	end?: string; // YYYY-MM-DD
	include_done?: boolean;
	journalDir?: string;
}

export async function readTasks(app: App, options: ReadTasksOptions = {}): Promise<string> {
	const today = moment();
	const startDate = options.start
		? moment(options.start, "YYYY-MM-DD", true)
		: today.clone().subtract(6, "days");
	const endDate = options.end
		? moment(options.end, "YYYY-MM-DD", true)
		: today.clone();

	if (!startDate.isValid() || !endDate.isValid()) {
		return "Error: Invalid date format for start or end date (expected YYYY-MM-DD).";
	}

	const includeDone = Boolean(options.include_done);
	const journalDir = options.journalDir || "journal";

	const lines: string[] = [
		`# Tasks from ${startDate.format("YYYY-MM-DD")} to ${endDate.format("YYYY-MM-DD")}\n`,
	];
	let foundAny = false;

	const cur = startDate.clone();
	while (cur.isSameOrBefore(endDate, "day")) {
		const dateISO = cur.format("YYYY-MM-DD");
		const relPath = dailyJournalPath(dateISO, journalDir);
		const file = app.vault.getAbstractFileByPath(relPath);

		if (file && file instanceof TFile) {
			const cache = app.metadataCache.getFileCache(file);
			const listItems = cache?.listItems || [];
			const taskItems = listItems.filter((item) => item.task !== undefined);

			if (taskItems.length > 0) {
				const content = await app.vault.cachedRead(file);
				const contentLines = content.split("\n");
				const dailyTasks: string[] = [];

				for (const item of taskItems) {
					const isDone = item.task!.toLowerCase() === "x";
					if (includeDone || !isDone) {
						const lineText = contentLines[item.position.start.line] || "";
						dailyTasks.push(lineText.trim());
					}
				}

				if (dailyTasks.length > 0) {
					foundAny = true;
					lines.push(`## [[${dateISO}]]`);
					for (const t of dailyTasks) {
						lines.push(t);
					}
					lines.push("");
				}
			}
		}

		cur.add(1, "day");
	}

	if (!foundAny) {
		return `No tasks found between ${startDate.format("YYYY-MM-DD")} and ${endDate.format("YYYY-MM-DD")}.`;
	}

	return lines.join("\n").trim();
}
