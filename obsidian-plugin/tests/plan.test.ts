import { describe, expect, it } from "vitest";
import { moment } from "obsidian";
import { buildPlan } from "../src/core/plan";

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
