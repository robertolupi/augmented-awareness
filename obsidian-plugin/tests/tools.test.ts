import { describe, it, expect, vi } from "vitest";
import { evaluateCalculation } from "../src/core/tools/calculator";
import { getDatetimeContext } from "../src/core/tools/datetime";
import { searchVault } from "../src/core/tools/search";
import { readPages } from "../src/core/tools/pages";
import { readTasks } from "../src/core/tools/tasks";
import {
	readJournal,
	readRetro,
	listDates,
	extractMetric,
} from "../src/core/tools/journal";
import { executeTool, CHAT_TOOLS } from "../src/core/tools/registry";
import { TFile, moment } from "obsidian";

function createMockFile(path: string, basename: string): TFile {
	const f = new (TFile as any)();
	f.path = path;
	f.basename = basename;
	return f;
}

describe("evaluateCalculation (Calculator Tool)", () => {
	it("evaluates basic arithmetic", () => {
		expect(evaluateCalculation("2 + 2 * 3")).toBe("8");
		expect(evaluateCalculation("(10 - 2) / 4")).toBe("2");
		expect(evaluateCalculation("2 ^ 3")).toBe("8");
		expect(evaluateCalculation("10 % 3")).toBe("1");
	});

	it("evaluates math functions", () => {
		expect(evaluateCalculation("sqrt(16)")).toBe("4");
		expect(evaluateCalculation("round(3.7)")).toBe("4");
		expect(evaluateCalculation("abs(-15)")).toBe("15");
		expect(evaluateCalculation("floor(4.9)")).toBe("4");
		expect(evaluateCalculation("ceil(4.1)")).toBe("5");
	});

	it("handles division by zero", () => {
		expect(evaluateCalculation("10 / 0")).toContain("Error: Division by zero");
	});

	it("evaluates date difference", () => {
		expect(evaluateCalculation('daysBetween("2026-10-01", "2026-10-05")')).toContain(
			"4 days (between 2026-10-01 and 2026-10-05)"
		);
		expect(evaluateCalculation('"2026-10-01" - "2026-10-10"')).toContain(
			"9 days (between 2026-10-01 and 2026-10-10)"
		);
	});

	it("evaluates date offsets", () => {
		expect(evaluateCalculation('addDays("2026-10-01", 7)')).toBe("2026-10-08");
		expect(evaluateCalculation('"2026-10-01" + 5 days')).toBe("2026-10-06");
		expect(evaluateCalculation('subDays("2026-10-10", 3)')).toBe("2026-10-07");
		expect(evaluateCalculation('"2026-10-10" - 2 days')).toBe("2026-10-08");
	});

	it("evaluates dayOfWeek and daysInMonth", () => {
		expect(evaluateCalculation('dayOfWeek("2026-10-03")')).toBe("Saturday");
		expect(evaluateCalculation("daysInMonth(2026, 2)")).toBe("28");
		expect(evaluateCalculation("daysInMonth(2024, 2)")).toBe("29");
	});
});

describe("getDatetimeContext", () => {
	it("returns formatted date and periodic note wikilinks", () => {
		const fixedDate = moment("2026-10-03 14:30:00", "YYYY-MM-DD HH:mm:ss");
		const output = getDatetimeContext(fixedDate);
		expect(output).toContain("Saturday, 2026-10-03 14:30:00");
		expect(output).toContain("[[Y2026]]");
		expect(output).toContain("[[2026-10]]");
		expect(output).toContain("[[2026-10-03]]");
		expect(output).toContain("[[2026-W40]]");
	});
});

describe("searchVault", () => {
	it("finds matching files by content and basename", async () => {
		const f1 = createMockFile("journal/2026/10/2026-10-02.md", "2026-10-02");
		const f2 = createMockFile("1-projects/Aww.md", "Aww");

		const mockFiles = [f1, f2];
		const mockContents: Record<string, string> = {
			"journal/2026/10/2026-10-02.md":
				"# Daily Notes\nWorking on deep learning and productivity improvements.",
			"1-projects/Aww.md":
				"# Augmented Awareness\nPlugin for Obsidian with smart agents.",
		};

		const mockApp: any = {
			vault: {
				getMarkdownFiles: () => mockFiles,
				cachedRead: vi.fn(async (file: TFile) => mockContents[file.path] || ""),
			},
			metadataCache: {
				getFileCache: () => null,
			},
		};

		const res = await searchVault(mockApp, { query: "productivity" });
		expect(res).toContain("Found 1 matching note(s)");
		expect(res).toContain("[[2026-10-02]]");
		expect(res).toContain("productivity");

		const resTitle = await searchVault(mockApp, { query: "Aww" });
		expect(resTitle).toContain("[[Aww]]");
	});

	it("returns helpful message when no matches found", async () => {
		const mockApp: any = {
			vault: {
				getMarkdownFiles: () => [],
				cachedRead: async () => "",
			},
		};
		const res = await searchVault(mockApp, { query: "nonexistent-query-xyz" });
		expect(res).toContain("No notes found");
	});
});

describe("readPages and resolveVaultPage", () => {
	it("resolves pages by link name, heading, and alias", async () => {
		const { resolveVaultPage } = await import("../src/core/tools/pages");
		const file = createMockFile("3-resources/Values.md", "Values");
		const mockApp: any = {
			vault: {
				getMarkdownFiles: () => [file],
				cachedRead: async () => "Integrity and Curiosity",
			},
			metadataCache: {
				getFirstLinkpathDest: (name: string) => (name === "Values" ? file : null),
			},
		};

		expect(resolveVaultPage(mockApp, "Values")?.basename).toBe("Values");
		expect(resolveVaultPage(mockApp, "[[Values]]")?.basename).toBe("Values");
		expect(resolveVaultPage(mockApp, "[[Values#Core Principles]]")?.basename).toBe("Values");
		expect(resolveVaultPage(mockApp, "[[Values|My Core Values]]")?.basename).toBe("Values");
		expect(resolveVaultPage(mockApp, "[[Values#Section|Alias]]")?.basename).toBe("Values");
		expect(resolveVaultPage(mockApp, "[[NonExistent]]")).toBeNull();
	});

	it("reads pages by link name or clean basename", async () => {
		const file = createMockFile("3-resources/Values.md", "Values");
		const mockApp: any = {
			vault: {
				getMarkdownFiles: () => [file],
				cachedRead: async () => "Integrity and Curiosity",
			},
			metadataCache: {
				getFirstLinkpathDest: (name: string) => (name === "Values" ? file : null),
			},
		};

		const res = await readPages(mockApp, ["[[Values]]", "Unknown"]);
		expect(res).toContain("# Values");
		expect(res).toContain("Integrity and Curiosity");
		expect(res).toContain("Page 'Unknown' not found in vault.");
	});
});

describe("readTasks", () => {
	it("extracts tasks and filters completed ones based on include_done", async () => {
		const dateISO = "2026-10-02";
		const file = createMockFile(`journal/2026/10/${dateISO}.md`, dateISO);
		const content = [
			"# 2026-10-02",
			"- [ ] Buy groceries",
			"- [x] Finish tests",
			"- [ ] Write documentation",
		].join("\n");

		const mockApp: any = {
			vault: {
				getAbstractFileByPath: (p: string) =>
					p.includes(dateISO) ? file : null,
				cachedRead: async () => content,
			},
			metadataCache: {
				getFileCache: () => ({
					listItems: [
						{ task: " ", position: { start: { line: 1 } } },
						{ task: "x", position: { start: { line: 2 } } },
						{ task: " ", position: { start: { line: 3 } } },
					],
				}),
			},
		};

		// Without include_done: only incomplete tasks
		const openOnly = await readTasks(mockApp, {
			start: "2026-10-02",
			end: "2026-10-02",
			include_done: false,
		});
		expect(openOnly).toContain("- [ ] Buy groceries");
		expect(openOnly).toContain("- [ ] Write documentation");
		expect(openOnly).not.toContain("- [x] Finish tests");

		// With include_done: all tasks
		const all = await readTasks(mockApp, {
			start: "2026-10-02",
			end: "2026-10-02",
			include_done: true,
		});
		expect(all).toContain("- [x] Finish tests");
	});
});

describe("journal tools", () => {
	it("extractMetric reads frontmatter metric", async () => {
		const dateISO = "2026-10-02";
		const file = createMockFile(`journal/2026/10/${dateISO}.md`, dateISO);
		const mockApp: any = {
			vault: {
				getAbstractFileByPath: (p: string) =>
					p.includes(dateISO) ? file : null,
			},
			metadataCache: {
				getFileCache: () => ({
					frontmatter: { stress: 4, mood: "Good" },
				}),
			},
		};

		const res = await extractMetric(mockApp, {
			metric: "stress",
			start: "2026-10-02",
			end: "2026-10-02",
		});
		expect(res).toBe("2026-10-02: 4");
	});

	it("listDates extracts tags and tasks", async () => {
		const dateISO = "2026-10-02";
		const jFile = createMockFile(`journal/2026/10/${dateISO}.md`, dateISO);
		const mockApp: any = {
			vault: {
				getAbstractFileByPath: (p: string) =>
					p.includes("journal") && p.includes(dateISO) ? jFile : null,
				cachedRead: async () => "- [ ] Review PR",
			},
			metadataCache: {
				getFileCache: () => ({
					tags: [{ tag: "#focus" }],
					frontmatter: { tags: ["dev", "aww"] },
					listItems: [{ task: " ", position: { start: { line: 0 } } }],
				}),
			},
		};

		const res = await listDates(mockApp, {
			start: "2026-10-02",
			end: "2026-10-02",
		});
		expect(res).toContain("2026-10-02: #aww, #dev, #focus");
		expect(res).toContain("- [ ] Review PR");
	});
});

describe("executeTool (Registry)", () => {
	it("registers all 9 core chat tools", () => {
		expect(CHAT_TOOLS.length).toBe(9);
		const names = CHAT_TOOLS.map((t) => t.function.name);
		expect(names).toContain("search_vault");
		expect(names).toContain("read_pages");
		expect(names).toContain("read_journal");
		expect(names).toContain("read_retro");
		expect(names).toContain("read_tasks");
		expect(names).toContain("list_dates");
		expect(names).toContain("extract_metric");
		expect(names).toContain("datetime");
		expect(names).toContain("calculator");
	});

	it("dispatches calculator and datetime tools", async () => {
		const mockApp: any = {
			vault: { getMarkdownFiles: () => [] },
		};
		const calcRes = await executeTool(
			"calculator",
			{ expression: "10 * 5 + 2" },
			{ app: mockApp }
		);
		expect(calcRes).toBe("52");

		const dtRes = await executeTool("datetime", {}, { app: mockApp });
		expect(dtRes).toContain("The pages relevant to today are:");
	});
});
