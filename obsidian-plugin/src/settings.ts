import { App, PluginSettingTab, Setting } from "obsidian";
import type AwwRetroPlugin from "./main";

export interface AwwRetroSettings {
	providerId: string;
	model: string;
	journalDir: string;
	retroDir: string;
}

export const DEFAULT_SETTINGS: AwwRetroSettings = {
	providerId: "",
	model: "",
	journalDir: "journal",
	retroDir: "retrospectives",
};

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

		new Setting(containerEl)
			.setName("Provider ID")
			.setDesc(
				"ID of the provider configured in the AI Providers plugin (see its settings)."
			)
			.addText((text) =>
				text
					.setPlaceholder("e.g. 1732815722182")
					.setValue(this.plugin.settings.providerId)
					.onChange(async (value) => {
						this.plugin.settings.providerId = value.trim();
						await this.plugin.saveSettings();
					})
			);

		new Setting(containerEl)
			.setName("Model")
			.setDesc(
				"Model override passed to the provider. Leave empty to use the provider's default model."
			)
			.addText((text) =>
				text
					.setPlaceholder("e.g. gpt-4o")
					.setValue(this.plugin.settings.model)
					.onChange(async (value) => {
						this.plugin.settings.model = value.trim();
						await this.plugin.saveSettings();
					})
			);

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
	}
}
