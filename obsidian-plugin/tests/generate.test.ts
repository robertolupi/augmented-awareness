import { describe, expect, it } from "vitest";
import { moment } from "obsidian";
import { ModelAdapter } from "../src/adapters/Model";
import { VaultStore } from "../src/adapters/VaultStore";
import { generateRetrospectives } from "../src/core/generate";
import { buildPlan } from "../src/core/plan";

class MemoryVaultStore implements VaultStore {
	files = new Map<string, string>();

	async exists(path: string): Promise<boolean> {
		return this.files.has(path);
	}

	async read(path: string): Promise<string> {
		const val = this.files.get(path);
		if (val === undefined) {
			throw new Error(`File not found: ${path}`);
		}
		return val;
	}

	async write(path: string, content: string): Promise<void> {
		this.files.set(path, content);
	}

	async rename(fromPath: string, toPath: string): Promise<void> {
		const val = await this.read(fromPath);
		this.files.delete(fromPath);
		this.files.set(toPath, val);
	}

	async ensureFolder(_dirPath: string): Promise<void> {}
}

class MockModelAdapter implements ModelAdapter {
	calls: { system: string; user: string }[] = [];

	async generate(
		system: string,
		user: string,
		signal?: AbortSignal
	): Promise<string> {
		if (signal?.aborted) {
			throw new DOMException("Generation cancelled", "AbortError");
		}
		this.calls.push({ system, user });
		return `Mock summary for:\n${user.slice(0, 100)}`;
	}
}

describe("generateRetrospectives", () => {
	it("generates a single daily retrospective", async () => {
		const vault = new MemoryVaultStore();
		const model = new MockModelAdapter();

		// Add daily journal
		await vault.write(
			"journal/2025/01/2025-01-08.md",
			"# Today\nGood day."
		);

		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "daily");

		const result = await generateRetrospectives({
			plan,
			model,
			vault,
			modelName: "test-model",
		});

		expect(result.created).toEqual([
			"retrospectives/2025/01/r2025-01-08.md",
		]);
		expect(result.reused).toEqual([]);
		expect(result.skipped).toEqual([]);
		expect(model.calls).toHaveLength(1);

		const createdFile = await vault.read(
			"retrospectives/2025/01/r2025-01-08.md"
		);
		expect(createdFile).toContain('model_name: "test-model"');
		expect(createdFile).toContain("# r2025-01-08");
		expect(createdFile).toContain('- "[[2025-01-08]]"');
	});


	it("reuses existing daily retrospectives when generating weekly", async () => {
		const vault = new MemoryVaultStore();
		const model = new MockModelAdapter();

		// Put all 7 daily retros in vault
		const weekDays = [
			"2025-01-06",
			"2025-01-07",
			"2025-01-08",
			"2025-01-09",
			"2025-01-10",
			"2025-01-11",
			"2025-01-12",
		];
		for (const d of weekDays) {
			await vault.write(
				`retrospectives/2025/01/r${d}.md`,
				`# r${d}\nDaily retro content for ${d}`
			);
		}

		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "weekly");

		const progressUpdates: string[] = [];
		const result = await generateRetrospectives({
			plan,
			model,
			vault,
			onProgress: (done, total, msg) => {
				progressUpdates.push(`[${done}/${total}] ${msg}`);
			},
		});

		// Exactly 1 model call for the weekly retro itself!
		expect(model.calls).toHaveLength(1);
		expect(result.created).toEqual([
			"retrospectives/2025/weeks/r2025-W02.md",
		]);
		expect(result.reused).toHaveLength(7);
		expect(result.skipped).toHaveLength(0);

		// Check weekly note content contains sources of daily retros
		const weeklyContent = await vault.read(
			"retrospectives/2025/weeks/r2025-W02.md"
		);
		expect(weeklyContent).toContain('# r2025-W02');
		expect(weeklyContent).toContain('sources:');
		expect(weeklyContent).toContain('- "[[r2025-01-08]]"');
	});

	it("skips missing daily journal files when generating weekly", async () => {
		const vault = new MemoryVaultStore();
		const model = new MockModelAdapter();

		// Only 2 daily journals exist in the week
		await vault.write(
			"journal/2025/01/2025-01-06.md",
			"Monday notes"
		);
		await vault.write(
			"journal/2025/01/2025-01-07.md",
			"Tuesday notes"
		);

		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "weekly");

		const result = await generateRetrospectives({
			plan,
			model,
			vault,
		});

		// 2 daily retros + 1 weekly retro = 3 calls
		expect(model.calls).toHaveLength(3);
		expect(result.created).toHaveLength(3);
		expect(result.skipped).toHaveLength(5); // 5 missing daily journals
	});

	it("aborts when AbortSignal is triggered", async () => {
		const vault = new MemoryVaultStore();
		const model = new MockModelAdapter();

		await vault.write(
			"journal/2025/01/2025-01-08.md",
			"Notes"
		);

		const abortController = new AbortController();
		abortController.abort(); // already aborted

		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "daily");

		await expect(
			generateRetrospectives({
				plan,
				model,
				vault,
				signal: abortController.signal,
			})
		).rejects.toThrow("Generation cancelled");
	});

	it("archives existing retrospective before recreating", async () => {
		const vault = new MemoryVaultStore();
		const model = new MockModelAdapter();

		await vault.write(
			"journal/2025/01/2025-01-08.md",
			"Notes"
		);
		// Pre-existing retrospective
		await vault.write(
			"retrospectives/2025/01/r2025-01-08.md",
			"Old retrospective content"
		);

		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "daily");

		await generateRetrospectives({
			plan,
			model,
			vault,
		});

		// Original path has new content
		expect(
			await vault.read("retrospectives/2025/01/r2025-01-08.md")
		).toContain("# r2025-01-08");

		// Old content archived to .1.md
		expect(
			await vault.read("retrospectives/2025/01/r2025-01-08.1.md")
		).toBe("Old retrospective content");
	});
});
