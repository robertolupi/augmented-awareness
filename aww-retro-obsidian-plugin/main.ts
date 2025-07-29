import { Plugin, TFile, Notice, PluginSettingTab, App, Setting, Editor, MarkdownView } from 'obsidian';

interface AwwRetroSettings {
	journalDir: string;
	retroDir: string;
}

const DEFAULT_SETTINGS: AwwRetroSettings = {
	journalDir: 'journal',
	retroDir: 'retrospectives',
}

export default class AwwRetro extends Plugin {
	settings: AwwRetroSettings;

	async onload() {
		console.log('loading AwwRetro plugin');
		await this.loadSettings();

		this.addSettingTab(new AwwRetroSettingTab(this.app, this));

		this.addCommand({
			id: 'open-retrospective',
			name: 'Open retrospective',
			editorCallback: (editor: Editor, view: MarkdownView) => {
				this.openRetrospective(view.file);
			}
		});
	}

	onunload() {
		console.log('unloading AwwRetro plugin');
	}

	async loadSettings() {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	async saveSettings() {
		await this.saveData(this.settings);
	}

	private isJournalFile(file: TFile): boolean {
		const journalRegex = /^\d{4}(-\d{2}(-\d{2})?|-W\d{2})?\.md$/;
		return file.path.startsWith(this.settings.journalDir) && journalRegex.test(file.name);
	}

	private getRetroPath(journalFile: TFile): string {
		const retroFileName = `r${journalFile.name}`;
		const retroFileDir = journalFile.parent.path.replace(this.settings.journalDir, this.settings.retroDir);
		return `${retroFileDir}/${retroFileName}`;
	}

	private async openRetrospective(file: TFile) {
		if (!this.isJournalFile(file)) {
			new Notice("Not a journal file.");
			return;
		}

		const retroFilePath = this.getRetroPath(file);
		let retroFile = this.app.vault.getAbstractFileByPath(retroFilePath);

		if ((retroFile instanceof TFile)) {
			const newLeaf = this.app.workspace.getLeaf(true);
			await newLeaf.openFile(retroFile as TFile);
		}

	}
}

class AwwRetroSettingTab extends PluginSettingTab {
	plugin: AwwRetro;

	constructor(app: App, plugin: AwwRetro) {
		super(app, plugin);
		this.plugin = plugin;
	}

	display(): void {
		const {containerEl} = this;

		containerEl.empty();

		containerEl.createEl('h2', {text: 'Aww Retrospectives Settings'});

		new Setting(containerEl)
			.setName('Journal directory')
			.setDesc('The directory where your journal notes are stored.')
			.addText(text => text
				.setPlaceholder('journal')
				.setValue(this.plugin.settings.journalDir)
				.onChange(async (value) => {
					this.plugin.settings.journalDir = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Retrospectives directory')
			.setDesc('The directory where your retrospective notes are stored.')
			.addText(text => text
				.setPlaceholder('retrospectives')
				.setValue(this.plugin.settings.retroDir)
				.onChange(async (value) => {
					this.plugin.settings.retroDir = value;
					await this.plugin.saveSettings();
				}));
	}
}
