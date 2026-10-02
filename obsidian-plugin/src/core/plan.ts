import { moment } from "obsidian";
import {
	ALL_LEVELS,
	Level,
	formatPeriod,
	wholeMonth,
	wholeWeek,
	wholeYear,
} from "./calendar";
import { journalPath, retroPath } from "./paths";

export interface PlanNode {
	key: string;
	level: Level;
	periodKey: string;
	date: moment.Moment;
	targetPath: string;
	targetName: string;
	journalPath: string;
	journalName: string;
	isRoot: boolean;
	sources: PlanNode[];
}

export interface Plan {
	root: PlanNode;
	nodes: PlanNode[]; // Topologically sorted, dependencies first
}

/**
 * Given a root date and level, expand the dates included in the selection.
 */
export function expandDatesForLevel(
	date: moment.Moment,
	level: Level
): string[] {
	switch (level) {
		case "daily":
			return [formatPeriod(date, "daily")];
		case "weekly":
			return wholeWeek(date);
		case "monthly":
			return wholeMonth(date);
		case "yearly":
			return wholeYear(date);
	}
}

/**
 * Build a dependency graph of retrospective nodes for the requested root period.
 */
export function buildPlan(
	rootDate: moment.Moment,
	rootLevel: Level,
	journalDir = "journal",
	retroDir = "retrospectives"
): Plan {
	const dates = expandDatesForLevel(rootDate, rootLevel);
	const nodeMap = new Map<string, PlanNode>();

	// Levels to include in the graph: up to and including rootLevel
	const levelIndex = ALL_LEVELS.indexOf(rootLevel);
	const activeLevels = ALL_LEVELS.slice(0, levelIndex + 1);

	// Root path to mark isRoot
	const rootTargetPath = retroPath(rootDate, rootLevel, retroDir);

	for (const dateStr of dates) {
		const d = moment(dateStr, "YYYY-MM-DD", true);

		for (const lvl of activeLevels) {
			const target = retroPath(d, lvl, retroDir);
			const targetBase = target.split("/").pop() ?? "";
			const targetName = targetBase.endsWith(".md")
				? targetBase.slice(0, -3)
				: targetBase;

			const journal = journalPath(d, lvl, journalDir);
			const journalBase = journal.split("/").pop() ?? "";
			const journalName = journalBase.endsWith(".md")
				? journalBase.slice(0, -3)
				: journalBase;

			let node = nodeMap.get(target);
			if (!node) {
				node = {
					key: target,
					level: lvl,
					periodKey: formatPeriod(d, lvl),
					date: d,
					targetPath: target,
					targetName,
					journalPath: journal,
					journalName,
					isRoot: target === rootTargetPath,
					sources: [],
				};
				nodeMap.set(target, node);
			}

			// Add lower level nodes as sources
			const currentLvlIndex = ALL_LEVELS.indexOf(lvl);
			for (let i = 0; i < currentLvlIndex; i++) {
				const lowerLvl = ALL_LEVELS[i];
				const lowerTarget = retroPath(d, lowerLvl, retroDir);
				const lowerNode = nodeMap.get(lowerTarget);
				if (lowerNode && !node.sources.includes(lowerNode)) {
					node.sources.push(lowerNode);
				}
			}
		}
	}

	const rootNode = nodeMap.get(rootTargetPath);
	if (!rootNode) {
		throw new Error(
			`Failed to find root node in plan for ${rootTargetPath}`
		);
	}

	// Sort sources within each node stably by targetName
	for (const node of nodeMap.values()) {
		node.sources.sort((a, b) => a.targetName.localeCompare(b.targetName));
	}

	// Topological sort: dependencies before parents
	const visited = new Set<string>();
	const orderedNodes: PlanNode[] = [];

	function visit(n: PlanNode) {
		if (visited.has(n.key)) {
			return;
		}
		visited.add(n.key);
		for (const src of n.sources) {
			visit(src);
		}
		orderedNodes.push(n);
	}

	visit(rootNode);

	return {
		root: rootNode,
		nodes: orderedNodes,
	};
}
