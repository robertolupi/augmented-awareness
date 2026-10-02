import { App, Modal, Notice, Setting, moment } from "obsidian";
import { ObsidianVaultStore } from "../adapters/VaultStore";
import { AIProvidersService } from "../adapters/Model";
import { Level } from "../core/calendar";
import { PlanAnalysis, analyzePlan, buildPlan } from "../core/plan";
import { getModelOptions, getProviderOptions } from "../settings";

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
		alwaysRegenerateRoot: boolean,
		providerId: string,
		model: string
	) => Promise<void>;
}

export class GenerateModal extends Modal {
	private date: moment.Moment;
	private level: Level;
	private providerId: string;
	private model: string;
	private alwaysRegenerateRoot = true;
	private modelContainerEl!: HTMLElement;
	private previewContainer!: HTMLElement;
	private generateBtn!: HTMLButtonElement;
	private vault: ObsidianVaultStore;

	constructor(private readonly options: GenerateModalOptions) {
		super(options.app);
		this.date = options.initialDate.clone();
		this.level = options.initialLevel;
		this.providerId = options.providerId || "";
		this.model = options.model || "";
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

		// 3. Provider setting
		const aiProviders = (
			this.app as App & { aiProviders?: AIProvidersService }
		).aiProviders;
		const providers = aiProviders?.providers ?? [];

		const providerSetting = new Setting(contentEl)
			.setName("Provider")
			.setDesc("Provider configured in the AI Providers plugin.");

		if (providers.length > 0) {
			providerSetting.addDropdown((dropdown) => {
				const providerOptions = getProviderOptions(providers);
				if (!this.providerId || !providerOptions[this.providerId]) {
					dropdown.addOption("", "-- Select a provider --");
				}
				for (const [id, label] of Object.entries(providerOptions)) {
					dropdown.addOption(id, label);
				}
				if (this.providerId && !providerOptions[this.providerId]) {
					dropdown.addOption(
						this.providerId,
						`${this.providerId} (configured)`
					);
				}
				dropdown.setValue(this.providerId);
				dropdown.onChange((value) => {
					this.providerId = value;
					const selected = providers.find((p) => p.id === value);
					this.model = selected?.model ?? "";
					this.renderModelSetting();
					void this.renderPreview();
				});
			});
		} else {
			providerSetting.setDesc(
				aiProviders
					? "No providers configured in AI Providers."
					: "AI Providers plugin is not available."
			);
			providerSetting.addText((text) => {
				text
					.setPlaceholder("e.g. id-1790951942041")
					.setValue(this.providerId)
					.onChange((value) => {
						this.providerId = value.trim();
						this.renderModelSetting();
						void this.renderPreview();
					});
			});
		}

		// 4. Model setting container
		this.modelContainerEl = contentEl.createDiv({
			cls: "aww-retro-modal-model-container",
		});
		this.renderModelSetting();

		// 5. Always regenerate root toggle
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

		// 6. Plan preview container
		this.previewContainer = contentEl.createDiv({
			cls: "aww-retro-modal-preview",
		});
		this.previewContainer.style.border =
			"1px solid var(--background-modifier-border)";
		this.previewContainer.style.borderRadius = "6px";
		this.previewContainer.style.padding = "12px";
		this.previewContainer.style.marginBottom = "16px";
		this.previewContainer.style.background = "var(--background-secondary)";

		// 7. Action buttons
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
			if (!this.providerId) {
				new Notice("Please select or enter an AI provider.");
				return;
			}
			this.close();
			await this.options.onGenerate(
				this.date,
				this.level,
				this.alwaysRegenerateRoot,
				this.providerId,
				this.model
			);
		});

		void this.renderPreview();
	}

	private renderModelSetting(): void {
		this.modelContainerEl.empty();

		const aiProviders = (
			this.app as App & { aiProviders?: AIProvidersService }
		).aiProviders;
		const providers = aiProviders?.providers ?? [];
		const selectedProvider = providers.find(
			(p) => p.id === this.providerId
		);

		const modelSetting = new Setting(this.modelContainerEl)
			.setName("Model")
			.setDesc("Model to use for retrospective generation.");

		const { hasChoices, options: modelOptions } = getModelOptions(
			selectedProvider,
			this.model
		);

		if (hasChoices) {
			modelSetting.addDropdown((dropdown) => {
				for (const [val, label] of Object.entries(modelOptions)) {
					dropdown.addOption(val, label);
				}
				if (modelOptions[this.model] !== undefined) {
					dropdown.setValue(this.model);
				} else {
					dropdown.setValue("");
				}
				dropdown.onChange((value) => {
					this.model = value;
					void this.renderPreview();
				});
			});
		} else {
			modelSetting.setDesc(
				"Model override passed to provider. Leave empty for provider default."
			);
			modelSetting.addText((text) => {
				text
					.setPlaceholder("e.g. gpt-4o")
					.setValue(this.model)
					.onChange((value) => {
						this.model = value.trim();
						void this.renderPreview();
					});
			});
		}
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

		const modelRow = this.previewContainer.createDiv();
		modelRow.style.marginBottom = "6px";
		modelRow.createEl("strong", { text: "Model: " });
		modelRow.createSpan({
			text: `${this.model || "default"} (Provider: ${
				this.providerId || "none"
			})`,
		});

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
