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

export interface NodeAnalysis {
	key: string;
	targetName: string;
	level: Level;
	status: "generate" | "reuse" | "skip";
	reason: string;
}

export interface PlanAnalysis {
	rootPath: string;
	rootName: string;
	rootExists: boolean;
	rootWillRegenerate: boolean;
	totalNodes: number;
	toGenerateCount: number;
	reusedCount: number;
	skippedCount: number;
	nodeDetails: NodeAnalysis[];
}

export async function analyzePlan(
	plan: Plan,
	vault: {
		exists(path: string): Promise<boolean>;
		mtime(path: string): Promise<number>;
	},
	alwaysRegenerateRoot = false
): Promise<PlanAnalysis> {
	const nodeDetails: NodeAnalysis[] = [];
	const needsGen = new Set<string>();
	let toGenerateCount = 0;
	let reusedCount = 0;
	let skippedCount = 0;

	for (const node of plan.nodes) {
		const targetExists = await vault.exists(node.targetPath);
		const journalExists = await vault.exists(node.journalPath);

		if (node.level === "daily" && !journalExists && !targetExists) {
			skippedCount++;
			nodeDetails.push({
				key: node.key,
				targetName: node.targetName,
				level: node.level,
				status: "skip",
				reason: "Missing daily journal file",
			});
			continue;
		}

		if (!targetExists) {
			needsGen.add(node.key);
			toGenerateCount++;
			nodeDetails.push({
				key: node.key,
				targetName: node.targetName,
				level: node.level,
				status: "generate",
				reason: "Retrospective note does not exist yet",
			});
			continue;
		}

		if (node.isRoot && alwaysRegenerateRoot) {
			needsGen.add(node.key);
			toGenerateCount++;
			nodeDetails.push({
				key: node.key,
				targetName: node.targetName,
				level: node.level,
				status: "generate",
				reason: "Forced root regeneration",
			});
			continue;
		}

		const targetMtime = await vault.mtime(node.targetPath);
		const journalMtime = journalExists
			? await vault.mtime(node.journalPath)
			: 0;

		if (journalMtime > targetMtime) {
			needsGen.add(node.key);
			toGenerateCount++;
			nodeDetails.push({
				key: node.key,
				targetName: node.targetName,
				level: node.level,
				status: "generate",
				reason: "Journal note modified after retrospective",
			});
			continue;
		}

		let sourceChanged = false;
		for (const src of node.sources) {
			if (needsGen.has(src.key)) {
				sourceChanged = true;
				break;
			}
			const srcMtime = await vault.mtime(src.targetPath);
			if (srcMtime > targetMtime) {
				sourceChanged = true;
				break;
			}
		}

		if (sourceChanged) {
			needsGen.add(node.key);
			toGenerateCount++;
			nodeDetails.push({
				key: node.key,
				targetName: node.targetName,
				level: node.level,
				status: "generate",
				reason: "Child dependency modified or regenerating",
			});
		} else {
			reusedCount++;
			nodeDetails.push({
				key: node.key,
				targetName: node.targetName,
				level: node.level,
				status: "reuse",
				reason: "Up to date with journal note",
			});
		}
	}

	const rootExists = await vault.exists(plan.root.targetPath);
	const rootWillRegenerate = needsGen.has(plan.root.key);

	return {
		rootPath: plan.root.targetPath,
		rootName: plan.root.targetName,
		rootExists,
		rootWillRegenerate,
		totalNodes: plan.nodes.length,
		toGenerateCount,
		reusedCount,
		skippedCount,
		nodeDetails,
	};
}

