import { describe, expect, it } from "vitest";
import { moment } from "obsidian";
import { analyzePlan, buildPlan } from "../src/core/plan";


describe("buildPlan", () => {
	it("builds a 1-node plan for daily level", () => {
		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "daily");

		expect(plan.root.level).toBe("daily");
		expect(plan.root.targetPath).toBe("retrospectives/2025/01/r2025-01-08.md");
		expect(plan.root.journalPath).toBe("journal/2025/01/2025-01-08.md");
		expect(plan.root.sources).toHaveLength(0);
		expect(plan.nodes).toHaveLength(1);
		expect(plan.nodes[0]).toBe(plan.root);
	});

	it("builds a weekly plan with 7 daily dependencies and 1 weekly root", () => {
		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "weekly");

		expect(plan.root.level).toBe("weekly");
		expect(plan.root.targetPath).toBe("retrospectives/2025/weeks/r2025-W02.md");
		expect(plan.root.journalPath).toBe("journal/2025/weeks/2025-W02.md");
		expect(plan.root.sources).toHaveLength(7);

		// 7 daily nodes + 1 weekly root = 8 nodes
		expect(plan.nodes).toHaveLength(8);
		// Root must be the last node (after all dependencies)
		expect(plan.nodes[7]).toBe(plan.root);

		// First 7 nodes must be daily
		for (let i = 0; i < 7; i++) {
			expect(plan.nodes[i].level).toBe("daily");
		}
		expect(plan.nodes[0].periodKey).toBe("2025-01-06");
		expect(plan.nodes[6].periodKey).toBe("2025-01-12");
	});

	it("builds a weekly plan crossing year boundary (week 1 2025)", () => {
		const m = moment("2024-12-31", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "weekly");

		expect(plan.root.targetPath).toBe("retrospectives/2025/weeks/r2025-W01.md");
		expect(plan.nodes).toHaveLength(8);
		expect(plan.nodes[0].targetPath).toBe("retrospectives/2024/12/r2024-12-30.md");
		expect(plan.nodes[6].targetPath).toBe("retrospectives/2025/01/r2025-01-05.md");
	});

	it("builds a monthly plan with daily, weekly, and monthly nodes deduplicated", () => {
		const m = moment("2025-01-15", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "monthly");

		expect(plan.root.level).toBe("monthly");
		expect(plan.root.targetPath).toBe("retrospectives/2025/months/r2025-01.md");

		// Last node is the monthly root
		expect(plan.nodes[plan.nodes.length - 1]).toBe(plan.root);

		// All keys in plan.nodes must be unique
		const keys = plan.nodes.map((n) => n.key);
		const uniqueKeys = new Set(keys);
		expect(uniqueKeys.size).toBe(keys.length);

		// Contains 31 daily nodes for January
		const dailyNodes = plan.nodes.filter((n) => n.level === "daily");
		expect(dailyNodes).toHaveLength(31);

		// Contains weekly nodes overlapping January
		const weeklyNodes = plan.nodes.filter((n) => n.level === "weekly");
		expect(weeklyNodes.length).toBeGreaterThan(0);
	});
});

describe("analyzePlan", () => {
	it("analyzes plan with missing journals, new notes, and up to date notes", async () => {
		const files = new Set<string>();
		const mtimes = new Map<string, number>();

		// 2025-01-06: Journal exists, no retro -> generate
		files.add("journal/2025/01/2025-01-06.md");
		mtimes.set("journal/2025/01/2025-01-06.md", 1000);

		// 2025-01-07: Journal exists, retro exists and is newer -> reuse
		files.add("journal/2025/01/2025-01-07.md");
		files.add("retrospectives/2025/01/r2025-01-07.md");
		mtimes.set("journal/2025/01/2025-01-07.md", 1000);
		mtimes.set("retrospectives/2025/01/r2025-01-07.md", 2000);

		// Other days (08..12): no journal, no retro -> skip

		const fakeVault = {
			exists: async (p: string) => files.has(p),
			mtime: async (p: string) => mtimes.get(p) ?? 0,
		};

		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "weekly");

		const analysis = await analyzePlan(plan, fakeVault, false);

		expect(analysis.rootPath).toBe("retrospectives/2025/weeks/r2025-W02.md");
		expect(analysis.rootExists).toBe(false);
		expect(analysis.rootWillRegenerate).toBe(true);
		expect(analysis.totalNodes).toBe(8);
		// 1 day (06) + 1 root (W02) = 2 to generate
		expect(analysis.toGenerateCount).toBe(2);
		// 1 day (07) reused
		expect(analysis.reusedCount).toBe(1);
		// 5 days skipped (no journal)
		expect(analysis.skippedCount).toBe(5);
	});

	it("skips weekly nodes that have no daily journal notes and no weekly journal", async () => {
		const files = new Set<string>();
		const mtimes = new Map<string, number>();

		// January 2025: only Jan 8 exists
		files.add("journal/2025/01/2025-01-08.md");
		mtimes.set("journal/2025/01/2025-01-08.md", 1000);

		const fakeVault = {
			exists: async (p: string) => files.has(p),
			mtime: async (p: string) => mtimes.get(p) ?? 0,
		};

		const m = moment("2025-01-15", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "monthly");

		const analysis = await analyzePlan(plan, fakeVault, false);

		// W01 (no notes), W03 (no notes), W05 (no notes) must be skipped
		const w01 = analysis.nodeDetails.find((n) => n.targetName === "r2025-W01");
		const w03 = analysis.nodeDetails.find((n) => n.targetName === "r2025-W03");
		const w05 = analysis.nodeDetails.find((n) => n.targetName === "r2025-W05");

		expect(w01?.status).toBe("skip");
		expect(w03?.status).toBe("skip");
		expect(w05?.status).toBe("skip");

		// W02 contains Jan 8, so W02 generates
		const w02 = analysis.nodeDetails.find((n) => n.targetName === "r2025-W02");
		expect(w02?.status).toBe("generate");

		// Month 2025-01 contains W02, so Month generates
		const root = analysis.nodeDetails.find((n) => n.targetName === "r2025-01");
		expect(root?.status).toBe("generate");
	});
});

