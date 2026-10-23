import { App, PluginSettingTab, Setting } from "obsidian";
import type AwwRetroPlugin from "./main";
import type { AIProviderEntry, AIProvidersService } from "./adapters/Model";

export interface AwwRetroSettings {
	providerId: string;
	model: string;
	journalDir: string;
	retroDir: string;
	/** Heading of the daily section holding time-tracking events. */
	journalSection: string;
	/** One heading per line; matching daily sections are removed from input. */
	ignoredHeadings: string;
	/** `key = template` lines; template may contain {} for the value. */
	metricTemplates: string;
	/** `tag: description` lines used as canonical tags in prompts. */
	canonicalTags: string;
}

// The full METRIC_FORMATTERS table from aww/retro_gen.py, verbatim and in
// table order.
export const DEFAULT_METRIC_TEMPLATES = [
	"stress = Stress level {} of 10.",
	"kg = Weight {} kg.",
	"bmi = Body Mass Index (BMI) {}.",
	"mood = Mood: {}",
	"meditation = Meditation: {}",
	"relax = Relax: {}",
	"career = Career: {}",
	"social = Social connections: {}",
	"exercise = Exercise: {}",
	"sleep_score = Sleep Score: {} of 100.",
	"vitals_score = Vitals Score: {} of 100.",
	"activity_score = Physical Activity Score: {} of 100.",
	"relax_score = Relax Score: {} of 100.",
	"pushups = Push-ups: {}",
	"exercise_time = Exercise Time: {} minutes",
].join("\n");

export const DEFAULT_SETTINGS: AwwRetroSettings = {
	providerId: "",
	model: "",
	journalDir: "journal",
	retroDir: "retrospectives",
	journalSection: "Journal and events",
	ignoredHeadings: "",
	metricTemplates: DEFAULT_METRIC_TEMPLATES,
	canonicalTags: "",
};

/** Parse the ignored-headings textarea: one heading per line. */
export function parseIgnoredHeadings(text: string): string[] {
	return text
		.split("\n")
		.map((line) => line.trim())
		.filter((line) => line.length > 0);
}

/**
 * Parse the metric-templates textarea into ordered [key, template] pairs.
 * Lines without `=` or with an empty key/template are skipped.
 */
export function parseMetricTemplates(text: string): [string, string][] {
	const out: [string, string][] = [];
	for (const raw of text.split("\n")) {
		const line = raw.trim();
		if (!line) {
			continue;
		}
		const eq = line.indexOf("=");
		if (eq < 0) {
			continue;
		}
		const key = line.slice(0, eq).trim();
		const template = line.slice(eq + 1).trim();
		if (key && template) {
			out.push([key, template]);
		}
	}
	return out;
}

/**
 * Parse the canonical-tags textarea into a record. Lines are
 * `tag: description`; a line without `:` is a tag with no description.
 */
export function parseCanonicalTags(text: string): Record<string, string> {
	const out: Record<string, string> = {};
	for (const raw of text.split("\n")) {
		const line = raw.trim();
		if (!line) {
			continue;
		}
		const idx = line.indexOf(":");
		if (idx < 0) {
			out[line] = "";
			continue;
		}
		const tag = line.slice(0, idx).trim();
		if (tag) {
			out[tag] = line.slice(idx + 1).trim();
		}
	}
	return out;
}

/**
 * Build a record of provider id -> display label for dropdown selection.
 */
export function getProviderOptions(
	providers: AIProviderEntry[]
): Record<string, string> {
	const out: Record<string, string> = {};
	for (const p of providers) {
		const label = p.name
			? p.type
				? `${p.name} (${p.type})`
				: p.name
			: p.id;
		out[p.id] = label;
	}
	return out;
}

export interface ModelOptionsResult {
	hasChoices: boolean;
	options: Record<string, string>;
}

/**
 * Build model choices for a given provider.
 * Returns hasChoices: false if the provider has no known models.
 */
export function getModelOptions(
	provider: AIProviderEntry | undefined,
	currentModel = ""
): ModelOptionsResult {
	if (!provider) {
		return { hasChoices: false, options: {} };
	}

	const modelSet = new Set<string>();
	if (provider.availableModels && Array.isArray(provider.availableModels)) {
		for (const m of provider.availableModels) {
			if (typeof m === "string" && m.trim()) {
				modelSet.add(m.trim());
			}
		}
	}
	if (provider.model && provider.model.trim()) {
		modelSet.add(provider.model.trim());
	}
	if (currentModel && currentModel.trim()) {
		modelSet.add(currentModel.trim());
	}

	if (modelSet.size === 0) {
		return { hasChoices: false, options: {} };
	}

	const options: Record<string, string> = {};
	const defaultLabel = provider.model
		? `Default (${provider.model})`
		: "Default";
	options[""] = defaultLabel;

	for (const m of Array.from(modelSet).sort()) {
		options[m] = m;
	}

	return { hasChoices: true, options };
}

export class AwwRetroSettingTab extends PluginSettingTab {
	constructor(
		app: App,
		private readonly plugin: AwwRetroPlugin
	) {
		super(app, plugin);
	}

	display(): void {
		const { containerEl } = this;
		containerEl.empty();

		const aiProviders = (
			this.app as App & { aiProviders?: AIProvidersService }
		).aiProviders;
		const providers = aiProviders?.providers ?? [];

		const providerSetting = new Setting(containerEl)
			.setName("Provider")
			.setDesc("Provider configured in the AI Providers plugin.");

		if (providers.length > 0) {
			providerSetting.addDropdown((dropdown) => {
				const providerOptions = getProviderOptions(providers);
				if (
					!this.plugin.settings.providerId ||
					!providerOptions[this.plugin.settings.providerId]
				) {
					dropdown.addOption("", "-- Select a provider --");
				}
				for (const [id, label] of Object.entries(providerOptions)) {
					dropdown.addOption(id, label);
				}
				if (
					this.plugin.settings.providerId &&
					!providerOptions[this.plugin.settings.providerId]
				) {
					dropdown.addOption(
						this.plugin.settings.providerId,
						`${this.plugin.settings.providerId} (saved)`
					);
				}
				dropdown.setValue(this.plugin.settings.providerId);
				dropdown.onChange(async (value) => {
					this.plugin.settings.providerId = value;
					const selected = providers.find((p) => p.id === value);
					this.plugin.settings.model = selected?.model ?? "";
					await this.plugin.saveSettings();
					this.display();
				});
			});
		} else {
			providerSetting.setDesc(
				aiProviders
					? "No providers configured in AI Providers. Configure a provider in AI Providers settings first."
					: "AI Providers plugin is not available. Install and enable it, then configure a provider."
			);
			providerSetting.addText((text) =>
				text
					.setPlaceholder("e.g. id-1790951942041")
					.setValue(this.plugin.settings.providerId)
					.onChange(async (value) => {
						this.plugin.settings.providerId = value.trim();
						await this.plugin.saveSettings();
					})
			);
		}

		const selectedProvider = providers.find(
			(p) => p.id === this.plugin.settings.providerId
		);
		const modelSetting = new Setting(containerEl)
			.setName("Model")
			.setDesc("Model to use for retrospective generation.");

		const { hasChoices, options: modelOptions } = getModelOptions(
			selectedProvider,
			this.plugin.settings.model
		);

		if (hasChoices) {
			modelSetting.addDropdown((dropdown) => {
				for (const [val, label] of Object.entries(modelOptions)) {
					dropdown.addOption(val, label);
				}
				if (modelOptions[this.plugin.settings.model] !== undefined) {
					dropdown.setValue(this.plugin.settings.model);
				} else {
					dropdown.setValue("");
				}
				dropdown.onChange(async (value) => {
					this.plugin.settings.model = value;
					await this.plugin.saveSettings();
				});
			});
		} else {
			modelSetting.setDesc(
				"Model override passed to the provider. Leave empty to use the provider's default model."
			);
			modelSetting.addText((text) =>
				text
					.setPlaceholder("e.g. gpt-4o")
					.setValue(this.plugin.settings.model)
					.onChange(async (value) => {
						this.plugin.settings.model = value.trim();
						await this.plugin.saveSettings();
					})
			);
		}

		new Setting(containerEl)
			.setName("Journal folder")
			.setDesc("Root folder containing daily journal notes.")
			.addText((text) =>
				text
					.setPlaceholder("journal")
					.setValue(this.plugin.settings.journalDir)
					.onChange(async (value) => {
						this.plugin.settings.journalDir =
							value.trim() || DEFAULT_SETTINGS.journalDir;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Retrospectives folder")
			.setDesc("Root folder where retrospective notes are created.")
			.addText((text) =>
				text
					.setPlaceholder("retrospectives")
					.setValue(this.plugin.settings.retroDir)
					.onChange(async (value) => {
						this.plugin.settings.retroDir =
							value.trim() || DEFAULT_SETTINGS.retroDir;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Journal events section")
			.setDesc(
				"Heading of the daily section holding time-tracking events (HH:MM lines)."
			)
			.addText((text) =>
				text
					.setPlaceholder("Journal and events")
					.setValue(this.plugin.settings.journalSection)
					.onChange(async (value) => {
						this.plugin.settings.journalSection =
							value.trim() || DEFAULT_SETTINGS.journalSection;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Ignored journal headings")
			.setDesc(
				"Daily sections with these headings are removed from the model input. One heading per line, case-insensitive."
			)
			.addTextArea((text) =>
				text
					.setPlaceholder("Ignored\nPrivate")
					.setValue(this.plugin.settings.ignoredHeadings)
					.onChange(async (value) => {
						this.plugin.settings.ignoredHeadings = value;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Frontmatter metrics")
			.setDesc(
				"Frontmatter keys appended to the model input, in this order. One `key = template` line each; {} is replaced by the value."
			)
			.addTextArea((text) =>
				text
					.setValue(this.plugin.settings.metricTemplates)
					.onChange(async (value) => {
						this.plugin.settings.metricTemplates = value;
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Canonical tags")
			.setDesc(
				"Tags listed in the retrospective prompt. One `tag: description` line each."
			)
			.addTextArea((text) =>
				text
					.setPlaceholder("health: physical or mental health")
					.setValue(this.plugin.settings.canonicalTags)
					.onChange(async (value) => {
						this.plugin.settings.canonicalTags = value;
						await this.plugin.saveSettings();
					})
			);
	}
}
