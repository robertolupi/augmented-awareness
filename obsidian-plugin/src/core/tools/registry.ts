/**
 * Tool registry and dispatcher for chat assistance.
 * Formats tool definitions for AI Providers toolsExecute (OpenAI-compatible schema).
 */
import { App } from "obsidian";
import { searchVault } from "./search";
import { readPages } from "./pages";
import { readTasks } from "./tasks";
import { readJournal, readRetro, listDates, extractMetric } from "./journal";
import { getDatetimeContext } from "./datetime";
import { evaluateCalculation } from "./calculator";

export interface ToolContext {
	app: App;
	journalDir?: string;
	retroDir?: string;
}

export interface OpenAIToolDefinition {
	type: "function";
	function: {
		name: string;
		description: string;
		parameters: {
			type: "object";
			properties: Record<string, any>;
			required?: string[];
		};
	};
}

export const CHAT_TOOLS: OpenAIToolDefinition[] = [
	{
		type: "function",
		function: {
			name: "search_vault",
			description:
				"Search for notes in the Obsidian vault using multi-word matching across note titles, paths, and contents. Returns relevant notes with matching snippets and [[wikilinks]].",
			parameters: {
				type: "object",
				properties: {
					query: {
						type: "string",
						description: "The search query (keywords, phrase, or topic).",
					},
					limit: {
						type: "number",
						description: "Maximum number of results to return (default 5, max 20).",
					},
				},
				required: ["query"],
			},
		},
	},
	{
		type: "function",
		function: {
			name: "read_pages",
			description:
				"Read one or more notes from the vault by name (e.g. ['2026-10-02', 'Personal Values Charter']) and return their full Markdown content including frontmatter.",
			parameters: {
				type: "object",
				properties: {
					pages: {
						type: "array",
						items: { type: "string" },
						description: "List of page names or [[wikilinks]] to read.",
					},
				},
				required: ["pages"],
			},
		},
	},
	{
		type: "function",
		function: {
			name: "read_journal",
			description:
				"Read the user's daily journal entries and retrospectives for the past 7 days up to and including today, preserving frontmatter metrics and sections.",
			parameters: {
				type: "object",
				properties: {},
			},
		},
	},
	{
		type: "function",
		function: {
			name: "read_retro",
			description:
				"Read today's retrospectives across all levels (daily, weekly, monthly, yearly) if they exist.",
			parameters: {
				type: "object",
				properties: {},
			},
		},
	},
	{
		type: "function",
		function: {
			name: "read_tasks",
			description:
				"Read tasks from daily journal notes in a date range using Obsidian's task index. Can include or exclude completed tasks.",
			parameters: {
				type: "object",
				properties: {
					start: {
						type: "string",
						description: "Start date in YYYY-MM-DD format (defaults to 6 days ago).",
					},
					end: {
						type: "string",
						description: "End date in YYYY-MM-DD format (defaults to today).",
					},
					include_done: {
						type: "boolean",
						description: "Whether to include completed tasks (default false).",
					},
				},
			},
		},
	},
	{
		type: "function",
		function: {
			name: "list_dates",
			description:
				"List all journal notes and retrospectives within a date range and extract hashtags and tasks from them.",
			parameters: {
				type: "object",
				properties: {
					start: {
						type: "string",
						description: "Start date (YYYY-MM-DD). Defaults to the first day of current month.",
					},
					end: {
						type: "string",
						description: "End date (YYYY-MM-DD). Defaults to the last day of current month.",
					},
				},
			},
		},
	},
	{
		type: "function",
		function: {
			name: "extract_metric",
			description:
				"List daily journal notes within a date range and extract a frontmatter metric from them (e.g. 'stress', 'mood', 'kg', 'sleep_score'). Days where the metric is missing are skipped.",
			parameters: {
				type: "object",
				properties: {
					metric: {
						type: "string",
						description: "Frontmatter field name to extract (e.g. 'stress', 'sleep_score').",
					},
					start: {
						type: "string",
						description: "Start date (YYYY-MM-DD). Defaults to first day of current month.",
					},
					end: {
						type: "string",
						description: "End date (YYYY-MM-DD). Defaults to last day of current month.",
					},
				},
				required: ["metric"],
			},
		},
	},
	{
		type: "function",
		function: {
			name: "datetime",
			description:
				"Get the current date and time along with wikilinks to relevant periodic notes for today (year, month, day, week).",
			parameters: {
				type: "object",
				properties: {},
			},
		},
	},
	{
		type: "function",
		function: {
			name: "calculator",
			description:
				"Safe arithmetic and date calculator. Supports math operations (+, -, *, /, %, ^, sqrt, round, abs) and date math (daysBetween('2026-10-01', '2026-10-05'), addDays('2026-10-01', 7), subDays('2026-10-01', 3), dayOfWeek('2026-10-03')).",
			parameters: {
				type: "object",
				properties: {
					expression: {
						type: "string",
						description: "The mathematical or date calculation expression to evaluate.",
					},
				},
				required: ["expression"],
			},
		},
	},
];

export async function executeTool(
	name: string,
	args: Record<string, any>,
	context: ToolContext
): Promise<string> {
	try {
		switch (name) {
			case "search_vault":
				return await searchVault(context.app, {
					query: args.query || "",
					limit: args.limit,
				});

			case "read_pages": {
				const pages = Array.isArray(args.pages) ? args.pages : [String(args.pages || "")];
				return await readPages(context.app, pages);
			}

			case "read_journal":
				return await readJournal(context.app, {
					journalDir: context.journalDir,
					retroDir: context.retroDir,
				});

			case "read_retro":
				return await readRetro(context.app, {
					journalDir: context.journalDir,
					retroDir: context.retroDir,
				});

			case "read_tasks":
				return await readTasks(context.app, {
					start: args.start,
					end: args.end,
					include_done: args.include_done,
					journalDir: context.journalDir,
				});

			case "list_dates":
				return await listDates(context.app, {
					start: args.start,
					end: args.end,
					journalDir: context.journalDir,
					retroDir: context.retroDir,
				});

			case "extract_metric":
				return await extractMetric(context.app, {
					metric: args.metric,
					start: args.start,
					end: args.end,
					journalDir: context.journalDir,
				});

			case "datetime":
				return getDatetimeContext();

			case "calculator":
				return evaluateCalculation(args.expression || "");

			default:
				return `Error: Unknown tool '${name}'.`;
		}
	} catch (err: any) {
		return `Error executing tool '${name}': ${err.message || String(err)}`;
	}
}
