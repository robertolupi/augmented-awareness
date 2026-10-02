import { App, Modal, Setting, moment } from "obsidian";
import { ObsidianVaultStore } from "../adapters/VaultStore";
import { Level } from "../core/calendar";
import { PlanAnalysis, analyzePlan, buildPlan } from "../core/plan";

export interface GenerateModalOptions {
	app: App;
	initialDate: moment.Moment;
	initialLevel: Level;
	journalDir: string;
	retroDir: string;
	providerId?: string;
	model?: string;
	onGenerate: (
		date: moment.Moment,
		level: Level,
		alwaysRegenerateRoot: boolean
	) => Promise<void>;
}

export class GenerateModal extends Modal {
	private date: moment.Moment;
	private level: Level;
	private alwaysRegenerateRoot = true;
	private previewContainer!: HTMLElement;
	private generateBtn!: HTMLButtonElement;
	private vault: ObsidianVaultStore;

	constructor(private readonly options: GenerateModalOptions) {
		super(options.app);
		this.date = options.initialDate.clone();
		this.level = options.initialLevel;
		this.vault = new ObsidianVaultStore(options.app);
	}

	onOpen(): void {
		const { contentEl } = this;
		contentEl.empty();
		this.titleEl.setText("Generate retrospective with options");

		// 1. Date setting
		new Setting(contentEl)
			.setName("Date")
			.setDesc("Base date for the retrospective (YYYY-MM-DD).")
			.addText((text) => {
				text.inputEl.type = "date";
				text.setValue(this.date.format("YYYY-MM-DD"));
				text.onChange((val) => {
					const parsed = moment(val, "YYYY-MM-DD", true);
					if (parsed.isValid()) {
						this.date = parsed;
						void this.renderPreview();
					}
				});
			});

		// 2. Level setting
		new Setting(contentEl)
			.setName("Period level")
			.setDesc("Select which retrospective period level to generate.")
			.addDropdown((dropdown) => {
				dropdown
					.addOption("daily", "Daily")
					.addOption("weekly", "Weekly")
					.addOption("monthly", "Monthly")
					.addOption("yearly", "Yearly")
					.setValue(this.level)
					.onChange((val) => {
						this.level = val as Level;
						void this.renderPreview();
					});
			});

		// 3. Always regenerate root toggle
		new Setting(contentEl)
			.setName("Force regenerate target")
			.setDesc(
				"Always regenerate the target retrospective even if its journal file has not changed (existing file will be archived)."
			)
			.addToggle((toggle) => {
				toggle
					.setValue(this.alwaysRegenerateRoot)
					.onChange((val) => {
						this.alwaysRegenerateRoot = val;
						void this.renderPreview();
					});
			});

		// 4. Model info
		if (this.options.providerId || this.options.model) {
			const infoEl = contentEl.createDiv({
				cls: "aww-retro-model-info",
			});
			infoEl.style.fontSize = "0.9em";
			infoEl.style.color = "var(--text-muted)";
			infoEl.style.marginBottom = "14px";
			infoEl.setText(
				`Model: ${this.options.model || "default"} (Provider: ${
					this.options.providerId || "none"
				})`
			);
		}

		// 5. Plan preview container
		this.previewContainer = contentEl.createDiv({
			cls: "aww-retro-modal-preview",
		});
		this.previewContainer.style.border =
			"1px solid var(--background-modifier-border)";
		this.previewContainer.style.borderRadius = "6px";
		this.previewContainer.style.padding = "12px";
		this.previewContainer.style.marginBottom = "16px";
		this.previewContainer.style.background = "var(--background-secondary)";

		// 6. Action buttons
		const btnRow = contentEl.createDiv({
			cls: "aww-retro-modal-actions",
		});
		btnRow.style.display = "flex";
		btnRow.style.justifyContent = "flex-end";
		btnRow.style.gap = "8px";

		const cancelBtn = btnRow.createEl("button", { text: "Cancel" });
		cancelBtn.addEventListener("click", () => this.close());

		this.generateBtn = btnRow.createEl("button", {
			text: "Generate retrospective",
			cls: "mod-cta",
		});
		this.generateBtn.addEventListener("click", async () => {
			this.close();
			await this.options.onGenerate(
				this.date,
				this.level,
				this.alwaysRegenerateRoot
			);
		});

		void this.renderPreview();
	}

	private async renderPreview(): Promise<void> {
		this.previewContainer.empty();

		const plan = buildPlan(
			this.date,
			this.level,
			this.options.journalDir,
			this.options.retroDir
		);

		const analysis: PlanAnalysis = await analyzePlan(
			plan,
			this.vault,
			this.alwaysRegenerateRoot
		);

		const title = this.previewContainer.createEl("h4", {
			text: "Plan Preview",
		});
		title.style.margin = "0 0 8px 0";

		const targetRow = this.previewContainer.createDiv();
		targetRow.style.marginBottom = "6px";
		targetRow.createEl("strong", { text: "Target: " });
		targetRow.createSpan({ text: analysis.rootPath });

		const statusRow = this.previewContainer.createDiv();
		statusRow.style.marginBottom = "8px";
		statusRow.createEl("strong", { text: "Status: " });
		if (!analysis.rootExists) {
			statusRow.createSpan({ text: "Will be created" });
		} else if (analysis.rootWillRegenerate) {
			statusRow.createSpan({
				text: "Will be regenerated (existing file will be archived)",
			});
		} else {
			statusRow.createSpan({
				text: "Already up to date (will be reused without model call)",
			});
		}

		const summaryRow = this.previewContainer.createDiv();
		summaryRow.style.marginBottom = "10px";
		summaryRow.createEl("strong", { text: "Estimated requests: " });
		summaryRow.createSpan({
			text: `${analysis.toGenerateCount} model call(s) (${analysis.reusedCount} reused, ${analysis.skippedCount} skipped)`,
		});

		// Node details list
		if (analysis.nodeDetails.length > 1) {
			const detailsEl = this.previewContainer.createEl("details");
			detailsEl.createEl("summary", {
				text: `View all ${analysis.totalNodes} dependencies`,
			});
			const ul = detailsEl.createEl("ul");
			ul.style.margin = "6px 0 0 16px";
			ul.style.padding = "0";
			ul.style.fontSize = "0.85em";

			for (const node of analysis.nodeDetails) {
				const li = ul.createEl("li");
				const badge =
					node.status === "generate"
						? "⚡ Generate"
						: node.status === "reuse"
						? "✓ Reuse"
						: "⊘ Skip";
				li.setText(`${node.targetName} [${badge}]: ${node.reason}`);
			}
		}
	}
}
