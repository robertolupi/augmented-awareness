import { ModelAdapter } from "../adapters/Model";
import { VaultStore } from "../adapters/VaultStore";
import { prepareInput } from "./input";
import { prepareOutput } from "./output";
import { findNextBackupPath, progressiveBackupPath } from "./paths";
import { Plan, PlanNode } from "./plan";
import { renderRetroPrompt } from "./prompts";

export interface GenerateOptions {
	plan: Plan;
	model: ModelAdapter;
	vault: VaultStore;
	canonicalTags?: Record<string, string>;
	ignoredHeadings?: string[];
	metricTemplates?: [string, string][];
	concurrencyLimit?: number;
	modelName?: string;
	signal?: AbortSignal;
	onProgress?: (completed: number, total: number, message: string) => void;
}

export interface GenerateResult {
	rootNode: PlanNode;
	created: string[];
	reused: string[];
	skipped: string[];
	cancelled: boolean;
	targetPath: string;
}

/**
 * Run a pool of async workers with a maximum concurrency limit.
 */
async function mapConcurrent<T, R>(
	items: T[],
	limit: number,
	fn: (item: T) => Promise<R>
): Promise<R[]> {
	if (items.length === 0) {
		return [];
	}
	const results: R[] = new Array(items.length);
	let nextIndex = 0;
	const workers = Array.from(
		{ length: Math.min(Math.max(1, limit), items.length) },
		async () => {
			while (nextIndex < items.length) {
				const index = nextIndex++;
				results[index] = await fn(items[index]);
			}
		}
	);
	await Promise.all(workers);
	return results;
}

/**
 * Find the next available backup path using the asynchronous VaultStore.
 */
async function getNextBackupPath(
	targetPath: string,
	vault: VaultStore
): Promise<string> {
	let i = 1;
	while (true) {
		const candidate = progressiveBackupPath(targetPath, i);
		if (!(await vault.exists(candidate))) {
			return candidate;
		}
		i++;
	}
}

/**
 * Format a retrospective note with frontmatter metadata and title.
 */
function formatNote(
	body: string,
	targetName: string,
	sourceItems: string[],
	modelName?: string
): string {
	const content = prepareOutput(body, targetName);
	const fm: string[] = ["---"];
	if (modelName) {
		fm.push(`model_name: ${JSON.stringify(modelName)}`);
	}
	fm.push(`ctime: ${JSON.stringify(new Date().toISOString())}`);
	if (sourceItems.length > 0) {
		fm.push("sources:");
		for (const src of sourceItems) {
			fm.push(`  - ${JSON.stringify(src)}`);
		}
	}
	fm.push("---", "");
	return fm.join("\n") + content;
}

export async function generateRetrospectives(
	options: GenerateOptions
): Promise<GenerateResult> {
	const {
		plan,
		model,
		vault,
		canonicalTags = {},
		ignoredHeadings = [],
		metricTemplates = [],
		concurrencyLimit = 5,
		modelName,
		signal,
		onProgress,
	} = options;

	if (signal?.aborted) {
		throw new DOMException("Generation cancelled", "AbortError");
	}

	const results = new Map<string, string>();
	const created: string[] = [];
	const reused: string[] = [];
	const skipped: string[] = [];

	// Group nodes by level: daily -> weekly -> monthly -> yearly
	const levels = ["daily", "weekly", "monthly", "yearly"] as const;
	const levelGroups = levels
		.map((lvl) => plan.nodes.filter((n) => n.level === lvl))
		.filter((group) => group.length > 0);

	// Count nodes needing generation for accurate progress
	const nodesNeedingGeneration: PlanNode[] = [];

	for (const group of levelGroups) {
		for (const node of group) {
			const targetExists = await vault.exists(node.targetPath);
			if (targetExists && !node.isRoot) {
				// Child node already generated and cached on disk
				reused.push(node.targetPath);
				const cached = await vault.read(node.targetPath);
				results.set(node.key, cached);
			} else if (
				node.level === "daily" &&
				!(await vault.exists(node.journalPath))
			) {
				// Daily journal file is missing, skip
				skipped.push(node.targetPath);
			} else {
				nodesNeedingGeneration.push(node);
			}
		}
	}

	const totalToGenerate = nodesNeedingGeneration.length;
	let completedCount = 0;

	if (totalToGenerate > 0) {
		onProgress?.(0, totalToGenerate, "Starting generation...");
	}

	for (const group of levelGroups) {
		if (signal?.aborted) {
			throw new DOMException("Generation cancelled", "AbortError");
		}

		// Only process nodes in this group that need generation
		const activeInGroup = group.filter((n) =>
			nodesNeedingGeneration.includes(n)
		);

		await mapConcurrent(
			activeInGroup,
			concurrencyLimit,
			async (node: PlanNode) => {
				if (signal?.aborted) {
					throw new DOMException("Generation cancelled", "AbortError");
				}

				onProgress?.(
					completedCount,
					totalToGenerate,
					`Generating ${node.targetName}...`
				);

				const sourceContents: string[] = [];
				const sourceItems: string[] = [];

				// Check same-level journal note
				if (await vault.exists(node.journalPath)) {
					const raw = await vault.read(node.journalPath);
					const cleaned = prepareInput(node.journalName, raw, {
						ignoredHeaders: ignoredHeadings,
						metrics: metricTemplates,
					});
					sourceContents.push(cleaned);
					sourceItems.push(`[[${node.journalName}]]`);
				}


				// Collect completed child retrospective contents
				for (const src of node.sources) {
					const srcContent = results.get(src.key);
					if (srcContent) {
						sourceContents.push(srcContent);
						sourceItems.push(`[[${src.targetName}]]`);
					}
				}

				if (sourceContents.length === 0) {
					// Nothing to generate from
					skipped.push(node.targetPath);
					return;
				}

				const userPrompt = sourceContents.join("\n\n");
				const systemPrompt = renderRetroPrompt(
					node.level,
					canonicalTags
				);

				const generatedText = await model.generate(
					systemPrompt,
					userPrompt,
					signal
				);

				if (signal?.aborted) {
					throw new DOMException("Generation cancelled", "AbortError");
				}

				// Archive existing target file if present
				if (await vault.exists(node.targetPath)) {
					const backupPath = await getNextBackupPath(
						node.targetPath,
						vault
					);
					await vault.rename(node.targetPath, backupPath);
				}

				const finalNote = formatNote(
					generatedText,
					node.targetName,
					sourceItems,
					modelName
				);
				await vault.write(node.targetPath, finalNote);
				results.set(node.key, finalNote);
				created.push(node.targetPath);

				completedCount++;
				onProgress?.(
					completedCount,
					totalToGenerate,
					`Completed ${node.targetName}`
				);
			}
		);
	}

	return {
		rootNode: plan.root,
		created,
		reused,
		skipped,
		cancelled: false,
		targetPath: plan.root.targetPath,
	};
}
