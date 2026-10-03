/**
 * Journal and retrospective query tools leveraging Obsidian's MetadataCache and Vault.
 */
import { App, TFile, moment } from "obsidian";
import { journalPath, retroPath } from "../paths";
import { Level } from "../calendar";
import { getDatetimeContext } from "./datetime";

export interface JournalToolOptions {
	journalDir?: string;
	retroDir?: string;
}

export async function readJournal(
	app: App,
	options: JournalToolOptions = {}
): Promise<string> {
	const journalDir = options.journalDir || "journal";
	const retroDir = options.retroDir || "retrospectives";
	const today = moment();

	const output: string[] = [
		getDatetimeContext(today),
		"\nThe user journal for the past week is as follows:\n",
	];

	for (let i = 0; i < 7; i++) {
		const d = today.clone().subtract(6 - i, "days");

		// Daily journal note
		const jPath = journalPath(d, "daily", journalDir);
		const jFile = app.vault.getAbstractFileByPath(jPath);
		if (jFile && jFile instanceof TFile) {
			const content = await app.vault.cachedRead(jFile);
			output.push(`# ${jFile.basename}\n${content}\n`);
		}

		// Daily retrospective note
		const rPath = retroPath(d, "daily", retroDir);
		const rFile = app.vault.getAbstractFileByPath(rPath);
		if (rFile && rFile instanceof TFile) {
			const content = await app.vault.cachedRead(rFile);
			output.push(`# ${rFile.basename}\n${content}\n`);
		}
	}

	return output.join("\n").trim();
}

export async function readRetro(
	app: App,
	options: JournalToolOptions = {}
): Promise<string> {
	const retroDir = options.retroDir || "retrospectives";
	const today = moment();
	const output: string[] = [];
	const levels: Level[] = ["daily", "weekly", "monthly", "yearly"];

	for (const level of levels) {
		const rPath = retroPath(today, level, retroDir);
		const rFile = app.vault.getAbstractFileByPath(rPath);
		if (rFile && rFile instanceof TFile) {
			const content = await app.vault.cachedRead(rFile);
			output.push(`# ${rFile.basename}\n${content}\n`);
		}
	}

	if (output.length === 0) {
		return "No retrospectives found for today.";
	}

	return output.join("\n").trim();
}

export interface ListDatesOptions extends JournalToolOptions {
	start?: string; // YYYY-MM-DD
	end?: string; // YYYY-MM-DD
}

export async function listDates(
	app: App,
	options: ListDatesOptions = {}
): Promise<string> {
	const today = moment();
	const startDate = options.start
		? moment(options.start, "YYYY-MM-DD", true)
		: today.clone().startOf("month");
	const endDate = options.end
		? moment(options.end, "YYYY-MM-DD", true)
		: today.clone().endOf("month");

	if (!startDate.isValid() || !endDate.isValid()) {
		return "Error: Invalid date format for start or end date (expected YYYY-MM-DD).";
	}

	const journalDir = options.journalDir || "journal";
	const retroDir = options.retroDir || "retrospectives";

	const journalOutput: string[] = [];
	const retroOutput: string[] = [];

	const cur = startDate.clone();
	while (cur.isSameOrBefore(endDate, "day")) {
		// Daily journal
		const jPath = journalPath(cur, "daily", journalDir);
		const jFile = app.vault.getAbstractFileByPath(jPath);
		if (jFile && jFile instanceof TFile) {
			const cache = app.metadataCache.getFileCache(jFile);
			const tags = collectTags(cache);
			const listItems = cache?.listItems || [];
			const taskItems = listItems.filter((item) => item.task !== undefined);

			if (tags.length > 0 || taskItems.length > 0) {
				if (tags.length > 0) {
					journalOutput.push(`${jFile.basename}: ${tags.join(", ")}`);
				} else {
					journalOutput.push(`${jFile.basename}:`);
				}

				if (taskItems.length > 0) {
					const content = await app.vault.cachedRead(jFile);
					const lines = content.split("\n");
					for (const item of taskItems) {
						const lineText = lines[item.position.start.line] || "";
						journalOutput.push(`  ${lineText.trim()}`);
					}
				}
			}
		}

		// Daily retro
		const rPath = retroPath(cur, "daily", retroDir);
		const rFile = app.vault.getAbstractFileByPath(rPath);
		if (rFile && rFile instanceof TFile) {
			const cache = app.metadataCache.getFileCache(rFile);
			const tags = collectTags(cache);
			if (tags.length > 0) {
				retroOutput.push(`${rFile.basename}: ${tags.join(", ")}`);
			}
		}

		cur.add(1, "day");
	}

	const output: string[] = [];
	if (journalOutput.length > 0) {
		output.push("Journal:");
		output.push(...journalOutput);
	}
	if (retroOutput.length > 0) {
		if (output.length > 0) output.push("");
		output.push("Retrospectives:");
		output.push(...retroOutput);
	}

	if (output.length === 0) {
		return `No tags or tasks found in the range ${startDate.format("YYYY-MM-DD")} to ${endDate.format("YYYY-MM-DD")}.`;
	}

	return output.join("\n");
}

export interface ExtractMetricOptions extends JournalToolOptions {
	metric: string;
	start?: string; // YYYY-MM-DD
	end?: string; // YYYY-MM-DD
}

export async function extractMetric(
	app: App,
	options: ExtractMetricOptions
): Promise<string> {
	if (!options.metric) {
		return "Error: Metric name is required.";
	}

	const today = moment();
	const startDate = options.start
		? moment(options.start, "YYYY-MM-DD", true)
		: today.clone().startOf("month");
	const endDate = options.end
		? moment(options.end, "YYYY-MM-DD", true)
		: today.clone().endOf("month");

	if (!startDate.isValid() || !endDate.isValid()) {
		return "Error: Invalid date format for start or end date (expected YYYY-MM-DD).";
	}

	const journalDir = options.journalDir || "journal";
	const results: string[] = [];

	const cur = startDate.clone();
	while (cur.isSameOrBefore(endDate, "day")) {
		const jPath = journalPath(cur, "daily", journalDir);
		const jFile = app.vault.getAbstractFileByPath(jPath);
		if (jFile && jFile instanceof TFile) {
			const cache = app.metadataCache.getFileCache(jFile);
			const fm = cache?.frontmatter;
			if (fm && fm[options.metric] !== undefined && fm[options.metric] !== null) {
				results.push(`${jFile.basename}: ${fm[options.metric]}`);
			}
		}
		cur.add(1, "day");
	}

	if (results.length === 0) {
		return `No values found for metric '${options.metric}' between ${startDate.format("YYYY-MM-DD")} and ${endDate.format("YYYY-MM-DD")}.`;
	}

	return results.join("\n");
}

function collectTags(cache: any): string[] {
	const tags = new Set<string>();
	if (cache?.tags) {
		for (const t of cache.tags) {
			if (t.tag) tags.add(t.tag.startsWith("#") ? t.tag : `#${t.tag}`);
		}
	}
	if (cache?.frontmatter?.tags) {
		const fmTags = cache.frontmatter.tags;
		if (Array.isArray(fmTags)) {
			for (const t of fmTags) {
				const s = String(t).trim();
				if (s) tags.add(s.startsWith("#") ? s : `#${s}`);
			}
		} else if (typeof fmTags === "string") {
			for (const t of fmTags.split(/[,\s]+/)) {
				const s = t.trim();
				if (s) tags.add(s.startsWith("#") ? s : `#${s}`);
			}
		}
	}
	return Array.from(tags).sort();
}
