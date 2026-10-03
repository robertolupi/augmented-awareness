import {
	ItemView,
	WorkspaceLeaf,
	TFile,
	Notice,
	MarkdownRenderer,
	setIcon,
	normalizePath,
} from "obsidian";
import type AwwRetroPlugin from "../main";
import type { AIProviderEntry, AIProvidersService } from "../adapters/Model";
import {
	ChatSession,
	createNewSession,
	saveChatToVault,
} from "../core/chat/session";
import { buildChatSystemPrompt } from "../core/chat/systemPrompt";
import {
	runChatAgent,
	ChatMessage,
	extractThinking,
	ChatCancelledError,
} from "../core/chat/agent";

export const CHAT_VIEW_TYPE = "aww-chat-view";

const THINK_RE = /<(?:think|thought)\b[^>]*>[\s\S]*?<\/(?:think|thought)>/gi;

export class AwwChatView extends ItemView {
	private plugin: AwwRetroPlugin;
	private activeSession: ChatSession;
	private isGenerating = false;
	private showToolCalls = false;
	private attachedNote: TFile | null = null;
	private abortController: AbortController | null = null;
	private currentIndicatorEl: HTMLElement | null = null;

	// UI elements
	private headerEl!: HTMLElement;
	private contextBarEl!: HTMLElement;
	private messagesContainerEl!: HTMLElement;
	private inputAreaEl!: HTMLElement;
	private textareaEl!: HTMLTextAreaElement;
	private sendBtnEl!: HTMLButtonElement;
	private stopBtnEl!: HTMLButtonElement;

	// Dropdown elements
	private sessionSelectEl!: HTMLSelectElement;
	private providerSelectEl!: HTMLSelectElement;
	private modelSelectEl!: HTMLSelectElement;

	constructor(leaf: WorkspaceLeaf, plugin: AwwRetroPlugin) {
		super(leaf);
		this.plugin = plugin;
		this.activeSession = this.getOrCreateActiveSession();
	}

	getViewType(): string {
		return CHAT_VIEW_TYPE;
	}

	getDisplayText(): string {
		return "Augmented Awareness Chat";
	}

	getIcon(): string {
		return "message-square";
	}

	async onOpen(): Promise<void> {
		const container = this.contentEl;
		container.empty();
		container.addClass("aww-chat-view-container");

		// Listen for active file changes so user can attach current note
		this.registerEvent(
			this.app.workspace.on("file-open", (file) => {
				if (file instanceof TFile && file.extension === "md") {
					// Update context button text if not pinned
					this.renderContextBar();
				}
			})
		);

		this.buildHeader(container);
		this.buildContextBar(container);
		this.buildMessagesContainer(container);
		this.buildInputArea(container);

		await this.renderMessages();
	}

	async onClose(): Promise<void> {
		if (this.abortController) {
			this.abortController.abort();
			this.abortController = null;
		}
	}

	private getOrCreateActiveSession(): ChatSession {
		const sessions = this.plugin.getChatSessions();
		const activeId = this.plugin.getActiveSessionId();
		let session = sessions.find((s) => s.id === activeId);
		if (!session) {
			session = sessions[0] || createNewSession("New Chat", this.plugin.settings.providerId, this.plugin.settings.model);
			this.plugin.saveChatSession(session);
		}
		return session;
	}

	private buildHeader(container: HTMLElement): void {
		this.headerEl = container.createDiv({ cls: "aww-chat-header" });

		// Row 1: Session Selector & Actions
		const sessionRow = this.headerEl.createDiv({ cls: "aww-chat-session-row" });

		this.sessionSelectEl = sessionRow.createEl("select", { cls: "dropdown aww-chat-session-select" });
		this.refreshSessionDropdown();
		this.sessionSelectEl.addEventListener("change", async () => {
			const id = this.sessionSelectEl.value;
			const target = this.plugin.getChatSessions().find((s) => s.id === id);
			if (target) {
				this.activeSession = target;
				this.plugin.setActiveSessionId(target.id);
				this.syncProviderDropdown();
				await this.renderMessages();
			}
		});

		// Action buttons
		const actionGroup = sessionRow.createDiv({ cls: "aww-chat-actions" });

		// New Session Button
		const newBtn = actionGroup.createEl("button", {
			cls: "clickable-icon",
			attr: { "aria-label": "New chat session" },
		});
		setIcon(newBtn, "plus");
		newBtn.addEventListener("click", async () => {
			const newSession = createNewSession(
				"New Chat",
				this.providerSelectEl?.value || this.plugin.settings.providerId,
				this.modelSelectEl?.value || this.plugin.settings.model
			);
			this.plugin.saveChatSession(newSession);
			this.activeSession = newSession;
			this.refreshSessionDropdown();
			await this.renderMessages();
		});

		// Save to Vault Button
		const saveBtn = actionGroup.createEl("button", {
			cls: "clickable-icon",
			attr: { "aria-label": "Save chat to Obsidian (Chats/)" },
		});
		setIcon(saveBtn, "save");
		saveBtn.addEventListener("click", async () => {
			await this.saveCurrentChatToVault();
		});

		// Rename Session Button
		const renameBtn = actionGroup.createEl("button", {
			cls: "clickable-icon",
			attr: { "aria-label": "Rename chat session" },
		});
		setIcon(renameBtn, "pencil");
		renameBtn.addEventListener("click", async () => {
			const current = this.activeSession.title || "Chat";
			const newTitle = prompt("Enter new title for this chat:", current);
			if (newTitle && newTitle.trim()) {
				this.activeSession.title = newTitle.trim();
				this.plugin.saveChatSession(this.activeSession);
				this.refreshSessionDropdown();
			}
		});

		// Delete Session Button
		const delBtn = actionGroup.createEl("button", {
			cls: "clickable-icon",
			attr: { "aria-label": "Delete chat session" },
		});
		setIcon(delBtn, "trash-2");
		delBtn.addEventListener("click", async () => {
			if (confirm(`Delete chat session "${this.activeSession.title}"?`)) {
				this.plugin.deleteChatSession(this.activeSession.id);
				this.activeSession = this.getOrCreateActiveSession();
				this.refreshSessionDropdown();
				await this.renderMessages();
			}
		});

		// Row 2: Provider & Model Selector + Tools toggle
		const providerRow = this.headerEl.createDiv({ cls: "aww-chat-provider-row" });

		this.providerSelectEl = providerRow.createEl("select", { cls: "dropdown aww-chat-provider-select" });
		this.modelSelectEl = providerRow.createEl("select", { cls: "dropdown aww-chat-model-select" });

		this.populateProvidersAndModels();

		this.providerSelectEl.addEventListener("change", () => {
			this.populateModelsForProvider(this.providerSelectEl.value);
			this.activeSession.providerId = this.providerSelectEl.value;
			this.activeSession.model = this.modelSelectEl.value;
			this.plugin.saveChatSession(this.activeSession);
		});

		this.modelSelectEl.addEventListener("change", () => {
			this.activeSession.model = this.modelSelectEl.value;
			this.plugin.saveChatSession(this.activeSession);
		});

		// Tool calls toggle
		const toolToggleLabel = providerRow.createEl("label", { cls: "aww-chat-tool-toggle" });
		const toolCheckbox = toolToggleLabel.createEl("input", { type: "checkbox" });
		toolCheckbox.checked = this.showToolCalls;
		toolToggleLabel.appendText(" Show tools");
		toolCheckbox.addEventListener("change", async () => {
			this.showToolCalls = toolCheckbox.checked;
			await this.renderMessages();
		});
	}

	private populateProvidersAndModels(): void {
		const aiProviders = (this.app as any).aiProviders as AIProvidersService | undefined;
		const providers = aiProviders?.providers || [];

		this.providerSelectEl.empty();
		if (providers.length === 0) {
			const opt = this.providerSelectEl.createEl("option", { text: "(No AI Providers found)", value: "" });
			opt.disabled = true;
			return;
		}

		for (const p of providers) {
			const label = p.name ? `${p.name} (${p.type || p.id})` : p.id;
			this.providerSelectEl.createEl("option", { text: label, value: p.id });
		}

		// Initial provider selection
		const initialProviderId =
			this.activeSession.providerId || this.plugin.settings.providerId || providers[0].id;
		if (providers.some((p) => p.id === initialProviderId)) {
			this.providerSelectEl.value = initialProviderId;
		} else {
			this.providerSelectEl.value = providers[0].id;
		}

		this.populateModelsForProvider(this.providerSelectEl.value);
	}

	private populateModelsForProvider(providerId: string): void {
		const aiProviders = (this.app as any).aiProviders as AIProvidersService | undefined;
		const provider = aiProviders?.providers?.find((p) => p.id === providerId);

		this.modelSelectEl.empty();
		if (!provider) return;

		const models = provider.availableModels && provider.availableModels.length > 0
			? provider.availableModels
			: provider.model ? [provider.model] : [];

		if (models.length === 0) {
			this.modelSelectEl.createEl("option", { text: "(Default model)", value: "" });
			return;
		}

		for (const m of models) {
			this.modelSelectEl.createEl("option", { text: m, value: m });
		}

		const initialModel = this.activeSession.model || this.plugin.settings.model || provider.model;
		if (models.includes(initialModel)) {
			this.modelSelectEl.value = initialModel;
		} else if (models[0]) {
			this.modelSelectEl.value = models[0];
		}
	}

	private syncProviderDropdown(): void {
		if (this.activeSession.providerId && this.providerSelectEl) {
			this.providerSelectEl.value = this.activeSession.providerId;
			this.populateModelsForProvider(this.activeSession.providerId);
			if (this.activeSession.model) {
				this.modelSelectEl.value = this.activeSession.model;
			}
		}
	}

	private refreshSessionDropdown(): void {
		this.sessionSelectEl.empty();
		const sessions = this.plugin.getChatSessions();
		for (const s of sessions) {
			const opt = this.sessionSelectEl.createEl("option", {
				text: s.title || "Untitled Chat",
				value: s.id,
			});
			if (s.id === this.activeSession.id) {
				opt.selected = true;
			}
		}
	}

	private buildContextBar(container: HTMLElement): void {
		this.contextBarEl = container.createDiv({ cls: "aww-chat-context-bar" });
		this.renderContextBar();
	}

	private renderContextBar(): void {
		this.contextBarEl.empty();
		const activeFile = this.app.workspace.getActiveFile();

		if (this.attachedNote) {
			const badge = this.contextBarEl.createDiv({ cls: "aww-chat-context-chip" });
			badge.createSpan({ text: `📎 [[${this.attachedNote.basename}]]` });
			const detachBtn = badge.createEl("button", {
				cls: "clickable-icon aww-chat-chip-remove",
				attr: { "aria-label": "Remove note context" },
			});
			setIcon(detachBtn, "x");
			detachBtn.addEventListener("click", () => {
				this.attachedNote = null;
				this.renderContextBar();
			});
		} else if (activeFile && activeFile instanceof TFile && activeFile.extension === "md") {
			const attachBtn = this.contextBarEl.createEl("button", {
				cls: "aww-chat-attach-btn",
				text: `+ Attach note: [[${activeFile.basename}]]`,
			});
			attachBtn.addEventListener("click", () => {
				this.attachedNote = activeFile;
				this.renderContextBar();
			});
		}
	}

	private buildMessagesContainer(container: HTMLElement): void {
		this.messagesContainerEl = container.createDiv({ cls: "aww-chat-messages" });
	}

	private async renderMessages(): Promise<void> {
		this.messagesContainerEl.empty();

		if (this.activeSession.messages.length === 0) {
			const emptyState = this.messagesContainerEl.createDiv({ cls: "aww-chat-empty-state" });
			emptyState.createEl("h4", { text: "Augmented Awareness Chat" });
			emptyState.createEl("p", {
				text: "Ask questions, explore journal entries, check open tasks, and reflect on your goals.",
			});

			const suggestions = emptyState.createDiv({ cls: "aww-chat-suggestions" });
			const prompts = [
				"What did I work on recently?",
				"List my uncompleted tasks",
				"Search vault for recent projects",
				"How has my stress level been?",
			];
			for (const p of prompts) {
				const chip = suggestions.createEl("button", { cls: "aww-chat-suggestion-chip", text: p });
				chip.addEventListener("click", () => {
					this.textareaEl.value = p;
					this.handleSendMessage();
				});
			}
			return;
		}

		for (const msg of this.activeSession.messages) {
			if (msg.role === "user") {
				const userBubble = this.messagesContainerEl.createDiv({ cls: "aww-chat-msg aww-chat-user" });
				userBubble.createDiv({ cls: "aww-chat-msg-header", text: "You" });
				const contentDiv = userBubble.createDiv({ cls: "aww-chat-msg-content" });
				contentDiv.setText(msg.content);
			} else if (msg.role === "assistant") {
				const { thoughts, content: cleanContent } = extractThinking(msg.content || "");
				const hasToolCalls = msg.tool_calls && msg.tool_calls.length > 0;

				// If it's an intermediate turn that called tools
				if (hasToolCalls) {
					// Render collapsed thought process if present
					for (const thought of thoughts) {
						const thoughtCard = this.messagesContainerEl.createEl("details", {
							cls: "aww-chat-thought-card",
						});
						thoughtCard.createEl("summary", {
							cls: "aww-chat-thought-summary",
							text: "💭 Thought process",
						});
						const body = thoughtCard.createDiv({ cls: "aww-chat-thought-body" });
						await MarkdownRenderer.render(this.app, thought, body, "", this);
					}

					if (this.showToolCalls) {
						for (const call of msg.tool_calls!) {
							const toolBubble = this.messagesContainerEl.createDiv({
								cls: "aww-chat-msg aww-chat-tool",
							});
							const toolCard = toolBubble.createEl("details", {
								cls: "aww-chat-tool-card",
							});
							const summary = toolCard.createEl("summary");
							summary.createSpan({ text: `🔧 Tool Call: ` });
							summary.createEl("b", { text: call.function?.name || "tool" });
							const body = toolCard.createDiv({ cls: "aww-chat-tool-body" });
							body.createEl("pre", { text: call.function?.arguments || "{}" });
						}
					}
					continue;
				}

				if (!cleanContent && thoughts.length === 0 && !msg.stopped) continue;

				const asstBubble = this.messagesContainerEl.createDiv({
					cls: "aww-chat-msg aww-chat-assistant",
				});
				asstBubble.createDiv({ cls: "aww-chat-msg-header", text: "Augmented Awareness" });

				// Render collapsed thought process at the top of the assistant bubble
				for (const thought of thoughts) {
					const thoughtCard = asstBubble.createEl("details", {
						cls: "aww-chat-thought-card",
					});
					thoughtCard.createEl("summary", {
						cls: "aww-chat-thought-summary",
						text: "💭 Thought process",
					});
					const body = thoughtCard.createDiv({ cls: "aww-chat-thought-body" });
					await MarkdownRenderer.render(this.app, thought, body, "", this);
				}

				if (cleanContent) {
					const contentDiv = asstBubble.createDiv({ cls: "aww-chat-msg-content" });
					await MarkdownRenderer.render(this.app, cleanContent, contentDiv, "", this);
				}

				if (msg.stopped) {
					const stopNotice = asstBubble.createDiv({
						cls: "aww-chat-stopped-notice",
					});
					const iconSpan = stopNotice.createSpan({
						cls: "aww-chat-stopped-icon",
					});
					setIcon(iconSpan, "square");
					stopNotice.createSpan({ text: "Generation stopped" });
				}
			} else if (msg.role === "tool" && this.showToolCalls) {
				const toolBubble = this.messagesContainerEl.createDiv({ cls: "aww-chat-msg aww-chat-tool" });
				const toolCard = toolBubble.createEl("details", { cls: "aww-chat-tool-card" });
				const summary = toolCard.createEl("summary");
				summary.createSpan({ text: `📋 Tool Output: ` });
				summary.createEl("b", { text: msg.tool_name || "tool" });
				const body = toolCard.createDiv({ cls: "aww-chat-tool-body" });
				body.createEl("pre", { text: msg.content });
			}
		}

		this.scrollToBottom();
	}

	private buildInputArea(container: HTMLElement): void {
		this.inputAreaEl = container.createDiv({ cls: "aww-chat-input-area" });

		this.textareaEl = this.inputAreaEl.createEl("textarea", {
			cls: "aww-chat-textarea",
			attr: {
				placeholder: "Ask about your notes, tasks, or reflections... (Enter to send, Shift+Enter for newline)",
				rows: "2",
			},
		});

		this.textareaEl.addEventListener("keydown", (e) => {
			if (e.key === "Enter" && !e.shiftKey) {
				e.preventDefault();
				this.handleSendMessage();
			}
		});

		const btnRow = this.inputAreaEl.createDiv({ cls: "aww-chat-btn-row" });

		this.stopBtnEl = btnRow.createEl("button", {
			cls: "mod-warning aww-chat-stop-btn",
			text: "Stop",
		});
		this.stopBtnEl.style.display = "none";
		this.stopBtnEl.addEventListener("click", () => {
			if (this.abortController) {
				this.stopBtnEl.setText("Stopping...");
				this.stopBtnEl.disabled = true;
				if (this.currentIndicatorEl) {
					this.currentIndicatorEl.setText("⏹ Stopping generation...");
				}
				this.abortController.abort();
			}
		});

		this.sendBtnEl = btnRow.createEl("button", {
			cls: "mod-cta aww-chat-send-btn",
			text: "Send",
		});
		this.sendBtnEl.addEventListener("click", () => {
			this.handleSendMessage();
		});
	}

	private async handleSendMessage(): Promise<void> {
		const prompt = this.textareaEl.value.trim();
		if (!prompt || this.isGenerating) return;

		this.textareaEl.value = "";

		// Add user message to session
		const userMsg: ChatMessage = {
			id: `user-${Date.now()}`,
			role: "user",
			content: prompt,
			timestamp: Date.now(),
		};
		this.activeSession.messages.push(userMsg);

		// If first message in untitled session, auto-title from prompt
		if (this.activeSession.title === "New Chat") {
			this.activeSession.title = prompt.slice(0, 30);
			this.refreshSessionDropdown();
		}

		this.plugin.saveChatSession(this.activeSession);
		await this.renderMessages();

		// Check selected provider
		const providerId = this.providerSelectEl.value || this.plugin.settings.providerId;
		const aiProviders = (this.app as any).aiProviders as AIProvidersService | undefined;
		const provider = aiProviders?.providers?.find((p) => p.id === providerId);

		if (!provider) {
			new Notice("No AI Provider selected or AI Providers is unavailable.");
			return;
		}

		const modelName = this.modelSelectEl.value || provider.model;

		// Set up generation state
		this.isGenerating = true;
		this.abortController = new AbortController();
		this.sendBtnEl.style.display = "none";
		this.stopBtnEl.setText("Stop");
		this.stopBtnEl.disabled = false;
		this.stopBtnEl.style.display = "inline-block";

		// Temporary indicator bubble
		this.currentIndicatorEl = this.messagesContainerEl.createDiv({
			cls: "aww-chat-msg aww-chat-assistant aww-chat-generating",
		});
		this.currentIndicatorEl.createSpan({ cls: "aww-chat-spinner", text: "● Thinking..." });
		this.scrollToBottom();

		try {
			// Read context note if attached
			let contextNoteData = null;
			if (this.attachedNote) {
				const noteContent = await this.app.vault.cachedRead(this.attachedNote);
				contextNoteData = {
					path: this.attachedNote.path,
					basename: this.attachedNote.basename,
					content: noteContent,
				};
			}

			const systemPrompt = await buildChatSystemPrompt(this.app, {
				contextNote: contextNoteData,
			});

			const result = await runChatAgent({
				app: this.app,
				provider,
				model: modelName,
				systemPrompt,
				messages: this.activeSession.messages,
				journalDir: this.plugin.settings.journalDir,
				retroDir: this.plugin.settings.retroDir,
				abortController: this.abortController,
				onProgress: (_chunk, accumulated) => {
					if (this.currentIndicatorEl) {
						this.currentIndicatorEl.setText(accumulated || "Thinking...");
						this.scrollToBottom();
					}
				},
				onToolCallStart: (toolName) => {
					if (this.currentIndicatorEl) {
						this.currentIndicatorEl.setText(`🔧 Using tool: ${toolName}...`);
						this.scrollToBottom();
					}
				},
			});

			// Append generated assistant/tool messages
			for (const m of result.generatedMessages) {
				this.activeSession.messages.push(m);
			}
			this.plugin.saveChatSession(this.activeSession);
		} catch (err: any) {
			const isCancelled =
				err instanceof ChatCancelledError ||
				err.name === "ChatCancelledError" ||
				err.message === "Chat generation cancelled.";

			if (isCancelled) {
				new Notice("Chat generation stopped.");
				const intermediate = err.generatedMessages || [];
				for (const m of intermediate) {
					this.activeSession.messages.push(m);
				}
				const partial = (err.partialContent || "").trim();
				const stoppedMsg: ChatMessage = {
					id: `asst-stopped-${Date.now()}`,
					role: "assistant",
					content: partial,
					timestamp: Date.now(),
					stopped: true,
				};
				this.activeSession.messages.push(stoppedMsg);
				this.plugin.saveChatSession(this.activeSession);
			} else {
				new Notice(`Chat error: ${err.message || String(err)}`);
				const errorMsg: ChatMessage = {
					id: `err-${Date.now()}`,
					role: "assistant",
					content: `⚠️ Error: ${err.message || String(err)}`,
					timestamp: Date.now(),
				};
				this.activeSession.messages.push(errorMsg);
				this.plugin.saveChatSession(this.activeSession);
			}
		} finally {
			if (this.currentIndicatorEl) {
				this.currentIndicatorEl.remove();
				this.currentIndicatorEl = null;
			}
			this.isGenerating = false;
			this.abortController = null;
			this.stopBtnEl.setText("Stop");
			this.stopBtnEl.disabled = false;
			this.sendBtnEl.style.display = "inline-block";
			this.stopBtnEl.style.display = "none";
			await this.renderMessages();
		}
	}

	private async saveCurrentChatToVault(): Promise<void> {
		if (this.activeSession.messages.length === 0) {
			new Notice("Chat is empty, nothing to save.");
			return;
		}

		try {
			const { file, path } = await saveChatToVault(this.app, this.activeSession, "Chats");
			new Notice(`Saved chat to ${path}`);
			// Open the note in Obsidian
			const leaf = this.app.workspace.getLeaf(true);
			if (leaf) {
				await leaf.openFile(file);
			}
		} catch (err: any) {
			new Notice(`Failed to save chat: ${err.message || String(err)}`);
		}
	}

	private scrollToBottom(): void {
		this.messagesContainerEl.scrollTop = this.messagesContainerEl.scrollHeight;
	}
}
