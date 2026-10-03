import { Notice, Plugin, TFile, moment, normalizePath } from "obsidian";
import { AIProvidersModelAdapter } from "./adapters/Model";
import { ObsidianVaultStore } from "./adapters/VaultStore";
import { Level } from "./core/calendar";
import { generateRetrospectives } from "./core/generate";
import { parseJournalOrRetroPath } from "./core/paths";
import { buildPlan } from "./core/plan";
import {
	AwwRetroSettingTab,
	AwwRetroSettings,
	DEFAULT_SETTINGS,
	parseCanonicalTags,
	parseIgnoredHeadings,
	parseMetricTemplates,
} from "./settings";
import { ProgressNotice } from "./ui/ProgressNotice";
import { GenerateModal } from "./ui/GenerateModal";
import { AwwChatView, CHAT_VIEW_TYPE } from "./ui/ChatView";
import type { ChatSession } from "./core/chat/session";


export default class AwwRetroPlugin extends Plugin {
	settings: AwwRetroSettings = { ...DEFAULT_SETTINGS };
	private activeAbortController?: AbortController;
	private chatSessions: ChatSession[] = [];
	private activeSessionId?: string;

	async onload() {
		await this.loadSettings();

		// Register Chat View
		this.registerView(
			CHAT_VIEW_TYPE,
			(leaf) => new AwwChatView(leaf, this)
		);

		// Ribbon icon to open chat
		this.addRibbonIcon(
			"message-square",
			"Open Augmented Awareness Chat",
			() => {
				void this.activateChatView();
			}
		);

		// Command to open chat
		this.addCommand({
			id: "open-chat",
			name: "Open chat",
			callback: () => {
				void this.activateChatView();
			},
		});

		this.addCommand({
			id: "generate-daily-retrospective",
			name: "Generate daily retrospective",
			callback: () => {
				void this.generateForLevel("daily");
			},
		});

		this.addCommand({
			id: "generate-weekly-retrospective",
			name: "Generate weekly retrospective",
			callback: () => {
				void this.generateForLevel("weekly");
			},
		});

		this.addCommand({
			id: "generate-monthly-retrospective",
			name: "Generate monthly retrospective",
			callback: () => {
				void this.generateForLevel("monthly");
			},
		});

		this.addCommand({
			id: "generate-yearly-retrospective",
			name: "Generate yearly retrospective",
			callback: () => {
				void this.generateForLevel("yearly");
			},
		});

		this.addCommand({
			id: "generate-retrospective-active-note",
			name: "Generate retrospective for active note",
			callback: () => {
				void this.generateRetrospectiveForActiveNote();
			},
		});

		this.addCommand({
			id: "generate-retrospective-options",
			name: "Generate retrospective with options...",
			callback: () => {
				this.openGenerateModal();
			},
		});

		this.addSettingTab(new AwwRetroSettingTab(this.app, this));
	}


	async onunload() {
		if (this.activeAbortController) {
			this.activeAbortController.abort();
			this.activeAbortController = undefined;
		}
	}

	async loadSettings() {
		const data = await this.loadData();
		this.settings = Object.assign(
			{},
			DEFAULT_SETTINGS,
			data
		);
		if (data && Array.isArray(data.chatSessions)) {
			this.chatSessions = data.chatSessions;
		}
		if (data && typeof data.activeSessionId === "string") {
			this.activeSessionId = data.activeSessionId;
		}
	}

	async saveSettings() {
		const data = {
			...this.settings,
			chatSessions: this.chatSessions,
			activeSessionId: this.activeSessionId,
		};
		await this.saveData(data);
	}

	async activateChatView(): Promise<void> {
		const { workspace } = this.app;
		let leaf = workspace.getLeavesOfType(CHAT_VIEW_TYPE)[0];
		if (!leaf) {
			const rightLeaf = workspace.getRightLeaf(false);
			if (rightLeaf) {
				await rightLeaf.setViewState({
					type: CHAT_VIEW_TYPE,
					active: true,
				});
				leaf = rightLeaf;
			}
		}
		if (leaf) {
			workspace.revealLeaf(leaf);
		}
	}

	getChatSessions(): ChatSession[] {
		return this.chatSessions;
	}

	getActiveSessionId(): string | undefined {
		return this.activeSessionId;
	}

	setActiveSessionId(id: string): void {
		this.activeSessionId = id;
		void this.saveSettings();
	}

	saveChatSession(session: ChatSession): void {
		const idx = this.chatSessions.findIndex((s) => s.id === session.id);
		if (idx >= 0) {
			this.chatSessions[idx] = session;
		} else {
			this.chatSessions.unshift(session);
		}
		this.activeSessionId = session.id;
		void this.saveSettings();
	}

	deleteChatSession(id: string): void {
		this.chatSessions = this.chatSessions.filter((s) => s.id !== id);
		if (this.activeSessionId === id) {
			this.activeSessionId = this.chatSessions[0]?.id;
		}
		void this.saveSettings();
	}

	private async generateForLevel(level: Level): Promise<void> {
		const activeFile = this.app.workspace.getActiveFile();
		let targetDate = moment();
		if (activeFile) {
			const parsed = parseJournalOrRetroPath(
				activeFile.path,
				this.settings.journalDir,
				this.settings.retroDir
			);
			if (parsed) {
				targetDate = parsed.date;
			}
		}
		await this.runGeneration(targetDate, level, false);
	}

	private async generateRetrospectiveForActiveNote(): Promise<void> {
		const activeFile = this.app.workspace.getActiveFile();
		if (!activeFile) {
			new Notice("No active note. Open a journal note first.");
			return;
		}

		const parsed = parseJournalOrRetroPath(
			activeFile.path,
			this.settings.journalDir,
			this.settings.retroDir
		);
		if (!parsed) {
			new Notice(
				`"${activeFile.path}" is not a recognized daily, weekly, monthly, or yearly note.`
			);
			return;
		}

		await this.runGeneration(parsed.date, parsed.level, true);
	}

	private openGenerateModal(): void {
		const activeFile = this.app.workspace.getActiveFile();
		let targetDate = moment();
		let initialLevel: Level = "daily";

		if (activeFile) {
			const parsed = parseJournalOrRetroPath(
				activeFile.path,
				this.settings.journalDir,
				this.settings.retroDir
			);
			if (parsed) {
				targetDate = parsed.date;
				initialLevel = parsed.level;
			}
		}

		new GenerateModal({
			app: this.app,
			initialDate: targetDate,
			initialLevel,
			journalDir: this.settings.journalDir,
			retroDir: this.settings.retroDir,
			providerId: this.settings.providerId,
			model: this.settings.model,
			onGenerate: async (
				date,
				level,
				alwaysRegenerateRoot,
				providerId,
				model
			) => {
				await this.runGeneration(
					date,
					level,
					alwaysRegenerateRoot,
					providerId,
					model
				);
			},
		}).open();
	}

	private async runGeneration(
		date: moment.Moment,
		level: Level,
		alwaysRegenerateRoot = false,
		overrideProviderId?: string,
		overrideModel?: string
	): Promise<void> {
		if (this.activeAbortController) {
			new Notice(
				"A retrospective generation is already running. Please cancel it or wait for it to finish."
			);
			return;
		}

		const effectiveProviderId =
			overrideProviderId || this.settings.providerId;
		const effectiveModel =
			overrideModel !== undefined ? overrideModel : this.settings.model;

		if (!effectiveProviderId) {
			new Notice(
				"No AI Providers provider ID configured. Set it in AWW Retrospectives settings or the generation options."
			);
			return;
		}

		const plan = buildPlan(
			date,
			level,
			this.settings.journalDir,
			this.settings.retroDir
		);

		const abortController = new AbortController();
		this.activeAbortController = abortController;

		const progress = new ProgressNotice(
			`Generating ${level} retrospective (${plan.root.periodKey})...`,
			plan.nodes.length,
			() => abortController.abort()
		);

		try {
			const model = new AIProvidersModelAdapter(
				this.app,
				effectiveProviderId,
				effectiveModel
			);
			const vault = new ObsidianVaultStore(this.app);

			const result = await generateRetrospectives({
				plan,
				model,
				vault,
				canonicalTags: parseCanonicalTags(this.settings.canonicalTags),
				ignoredHeadings: parseIgnoredHeadings(
					this.settings.ignoredHeadings
				),
				metricTemplates: parseMetricTemplates(
					this.settings.metricTemplates
				),
				concurrencyLimit: 5,
				modelName: effectiveModel || effectiveProviderId,
				signal: abortController.signal,
				alwaysRegenerateRoot,
				onProgress: (completed, total, message) => {
					progress.update(completed, total, message);
				},
			});

			if (result.upToDate) {
				progress.complete(
					`Retrospective is already up to date: ${result.targetPath}`
				);
			} else {
				progress.complete(`Retrospective created: ${result.targetPath}`);
			}

			const createdFile = this.app.vault.getAbstractFileByPath(
				normalizePath(result.targetPath)
			);
			if (createdFile instanceof TFile) {
				await this.app.workspace.getLeaf().openFile(createdFile);
			}

		} catch (err) {
			if (
				abortController.signal.aborted ||
				(err instanceof Error && err.name === "AbortError")
			) {
				progress.cancel();
			} else {
				const msg = err instanceof Error ? err.message : String(err);
				progress.error(msg);
			}
		} finally {
			this.activeAbortController = undefined;
		}
	}
}
