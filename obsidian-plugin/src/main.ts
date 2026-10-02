import { Notice, Plugin, normalizePath } from "obsidian";
import { dailyRetroPath, parseDailyJournalPath } from "./core/paths";
import { prepareInput } from "./core/input";
import { prepareOutput } from "./core/output";
import {
	buildTagsBlock,
	canonicalTagNames,
	renderTemplate,
} from "./core/prompts";
import { AIProvidersModelAdapter, ModelError } from "./adapters/Model";
import {
	AwwRetroSettingTab,
	AwwRetroSettings,
	DEFAULT_SETTINGS,
	parseCanonicalTags,
	parseIgnoredHeadings,
	parseMetricTemplates,
} from "./settings";
import dailyPrompt from "./prompts/daily.md";

export default class AwwRetroPlugin extends Plugin {
	settings: AwwRetroSettings = { ...DEFAULT_SETTINGS };

	async onload() {
		await this.loadSettings();

		this.addCommand({
			id: "generate-retrospective-active-note",
			name: "Generate retrospective for active note",
			callback: () => {
				void this.generateRetrospectiveForActiveNote();
			},
		});

		this.addSettingTab(new AwwRetroSettingTab(this.app, this));
	}

	async loadSettings() {
		this.settings = Object.assign(
			{},
			DEFAULT_SETTINGS,
			await this.loadData()
		);
	}

	async saveSettings() {
		await this.saveData(this.settings);
	}

	private async generateRetrospectiveForActiveNote(): Promise<void> {
		const file = this.app.workspace.getActiveFile();
		if (!file) {
			new Notice("No active note. Open a daily journal note first.");
			return;
		}

		const dateISO = parseDailyJournalPath(
			file.path,
			this.settings.journalDir
		);
		if (!dateISO) {
			new Notice(
				`"${file.path}" is not a daily journal note (expected ${this.settings.journalDir}/<yyyy>/<mm>/<yyyy-mm-dd>.md).`
			);
			return;
		}

		const targetPath = dailyRetroPath(
			dateISO,
			this.settings.journalDir,
			this.settings.retroDir
		);
		if (this.app.vault.getAbstractFileByPath(targetPath)) {
			new Notice(`Retrospective already exists: ${targetPath}`);
			return;
		}

		if (!this.settings.providerId) {
			new Notice(
				"No AI Providers provider ID configured. Set it in AWW Retrospectives settings."
			);
			return;
		}

		const adapter = new AIProvidersModelAdapter(
			this.app,
			this.settings.providerId,
			this.settings.model
		);

		new Notice(`Generating retrospective for ${dateISO}...`);
		const rawContent = await this.app.vault.read(file);

		const tags = parseCanonicalTags(this.settings.canonicalTags);
		const systemPrompt = renderTemplate(dailyPrompt, {
			canonical_tags: canonicalTagNames(tags),
			canonical_tags_block: buildTagsBlock(tags),
		});
		const userMessage = prepareInput(file.basename, rawContent, {
			ignoredHeaders: parseIgnoredHeadings(this.settings.ignoredHeadings),
			metrics: parseMetricTemplates(this.settings.metricTemplates),
		});

		let generated: string;
		try {
			generated = await adapter.generate(systemPrompt, userMessage);
		} catch (err) {
			const message =
				err instanceof ModelError || err instanceof Error
					? err.message
					: String(err);
			new Notice(`Retrospective generation failed: ${message}`);
			return;
		}

		try {
			const parentDir = targetPath.slice(
				0,
				targetPath.lastIndexOf("/")
			);
			if (!this.app.vault.getAbstractFileByPath(parentDir)) {
				await this.app.vault.createFolder(parentDir);
			}
			const created = await this.app.vault.create(
				normalizePath(targetPath),
				prepareOutput(generated, `r${dateISO}`)
			);
			await this.app.workspace.getLeaf().openFile(created);
			new Notice(`Retrospective created: ${targetPath}`);
		} catch (err) {
			new Notice(
				`Failed to save retrospective: ${
					err instanceof Error ? err.message : String(err)
				}`
			);
		}
	}
}
