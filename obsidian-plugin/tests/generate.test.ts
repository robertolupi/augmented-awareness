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

	mtimes = new Map<string, number>();

	setMtime(path: string, time: number): void {
		this.mtimes.set(path, time);
	}

	async mtime(path: string): Promise<number> {
		return this.mtimes.get(path) ?? (this.files.has(path) ? 1000 : 0);
	}
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
			alwaysRegenerateRoot: true,
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

	it("regenerates dependency when its daily journal file is newer than the retrospective", async () => {
		const vault = new MemoryVaultStore();
		const model = new MockModelAdapter();

		// Put all 7 daily retros in vault with mtime 1000
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
			const retroP = `retrospectives/2025/01/r${d}.md`;
			await vault.write(retroP, `# r${d}\nOld retro`);
			vault.setMtime(retroP, 1000);
		}

		// Existing weekly retro with mtime 1000
		const weeklyP = "retrospectives/2025/weeks/r2025-W02.md";
		await vault.write(weeklyP, "# r2025-W02\nOld weekly retro");
		vault.setMtime(weeklyP, 1000);

		// Now update 2025-01-08 journal note with newer mtime 2000
		const changedJournal = "journal/2025/01/2025-01-08.md";
		await vault.write(changedJournal, "# 2025-01-08\nUpdated thoughts!");
		vault.setMtime(changedJournal, 2000);

		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "weekly");

		const result = await generateRetrospectives({
			plan,
			model,
			vault,
			alwaysRegenerateRoot: false,
		});

		// 1 daily retro (2025-01-08) + 1 weekly retro = 2 calls
		expect(model.calls).toHaveLength(2);
		expect(result.created).toContain("retrospectives/2025/01/r2025-01-08.md");
		expect(result.created).toContain("retrospectives/2025/weeks/r2025-W02.md");
		expect(result.reused).toHaveLength(6); // other 6 days reused
		expect(result.upToDate).toBe(false);
	});

	it("reuses all retrospectives when everything is up to date and alwaysRegenerateRoot is false", async () => {
		const vault = new MemoryVaultStore();
		const model = new MockModelAdapter();

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
			const retroP = `retrospectives/2025/01/r${d}.md`;
			const journalP = `journal/2025/01/${d}.md`;
			await vault.write(retroP, `# r${d}`);
			await vault.write(journalP, `# ${d}`);
			vault.setMtime(retroP, 2000); // retro is newer
			vault.setMtime(journalP, 1000); // journal is older
		}

		const weeklyP = "retrospectives/2025/weeks/r2025-W02.md";
		await vault.write(weeklyP, "# r2025-W02");
		vault.setMtime(weeklyP, 3000);

		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "weekly");

		const result = await generateRetrospectives({
			plan,
			model,
			vault,
			alwaysRegenerateRoot: false,
		});

		// Zero model calls!
		expect(model.calls).toHaveLength(0);
		expect(result.created).toHaveLength(0);
		expect(result.upToDate).toBe(true);
		expect(result.reused).toHaveLength(8); // 7 daily + 1 weekly
	});

	it("forces root generation when alwaysRegenerateRoot is true even if up to date", async () => {
		const vault = new MemoryVaultStore();
		const model = new MockModelAdapter();

		const dailyRetro = "retrospectives/2025/01/r2025-01-08.md";
		const dailyJournal = "journal/2025/01/2025-01-08.md";
		await vault.write(dailyRetro, "# r2025-01-08");
		await vault.write(dailyJournal, "# 2025-01-08");
		vault.setMtime(dailyRetro, 2000);
		vault.setMtime(dailyJournal, 1000);

		const m = moment("2025-01-08", "YYYY-MM-DD", true);
		const plan = buildPlan(m, "daily");

		const result = await generateRetrospectives({
			plan,
			model,
			vault,
			alwaysRegenerateRoot: true,
		});

		// 1 model call because alwaysRegenerateRoot is true
		expect(model.calls).toHaveLength(1);
		expect(result.created).toEqual([dailyRetro]);
		expect(result.upToDate).toBe(false);
	});
});

