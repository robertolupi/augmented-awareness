import { describe, it, expect, vi } from "vitest";
import {
	createNewSession,
	formatChatMarkdown,
	saveChatToVault,
} from "../src/core/chat/session";
import { buildChatSystemPrompt } from "../src/core/chat/systemPrompt";
import { TFile } from "obsidian";

describe("Chat Session Management", () => {
	it("creates a new session with defaults", () => {
		const session = createNewSession("Trip Planning", "lmstudio", "model-1");
		expect(session.id).toContain("chat-");
		expect(session.title).toBe("Trip Planning");
		expect(session.providerId).toBe("lmstudio");
		expect(session.model).toBe("model-1");
		expect(session.messages).toEqual([]);
	});

	it("formats chat history as Markdown matching Streamlit export", () => {
		const session = createNewSession("Weekly Review", "openrouter", "deepseek");
		session.messages.push({
			id: "1",
			role: "user",
			content: "What did I work on this week?",
			timestamp: 1000,
		});
		session.messages.push({
			id: "2",
			role: "assistant",
			content: "You worked on the Obsidian plugin and tasks.",
			timestamp: 2000,
		});

		const md = formatChatMarkdown(session);
		expect(md).toContain("# Weekly Review");
		expect(md).toContain("### User\nWhat did I work on this week?");
		expect(md).toContain(
			"### AI\nYou worked on the Obsidian plugin and tasks."
		);
		expect(md).toContain("Model: `deepseek`");
	});

	it("saves chat session to vault under Chats/ directory", async () => {
		const session = createNewSession("Goals 2026");
		session.messages.push({
			id: "1",
			role: "user",
			content: "Set 3 goals",
			timestamp: 1000,
		});
		session.messages.push({
			id: "2",
			role: "assistant",
			content: "1. Health, 2. Focus, 3. Community",
			timestamp: 2000,
		});

		let folderCreated = false;
		let fileCreatedPath = "";
		let fileCreatedContent = "";

		const mockFile = new TFile();
		const mockApp: any = {
			vault: {
				getAbstractFileByPath: (p: string) => null,
				createFolder: vi.fn(async (folder: string) => {
					folderCreated = true;
				}),
				create: vi.fn(async (path: string, content: string) => {
					fileCreatedPath = path;
					fileCreatedContent = content;
					return mockFile;
				}),
				modify: vi.fn(),
			},
		};

		const res = await saveChatToVault(mockApp, session, "Chats");
		expect(mockApp.vault.createFolder).toHaveBeenCalledWith("Chats");
		expect(mockApp.vault.create).toHaveBeenCalled();
		expect(res.path).toContain("Chats/");
		expect(res.path).toContain("Goals 2026.md");
		expect(fileCreatedContent).toContain("# Goals 2026");
	});
});

describe("buildChatSystemPrompt", () => {
	it("includes tool instructions, datetime, and optional context note", async () => {
		const mockApp: any = {
			vault: {
				getMarkdownFiles: () => [],
			},
			metadataCache: {
				getFirstLinkpathDest: () => null,
			},
		};

		const prompt = await buildChatSystemPrompt(mockApp, {
			contextNote: {
				path: "journal/2026/10/2026-10-02.md",
				basename: "2026-10-02",
				content: "# Daily Note\nFocus day.",
			},
		});

		expect(prompt).toContain("Augmented Awareness (aww)");
		expect(prompt).toContain("search_vault");
		expect(prompt).toContain("read_journal");
		expect(prompt).toContain("Active Note Context:");
		expect(prompt).toContain("[[2026-10-02]]");
		expect(prompt).toContain("Focus day.");
	});
});

describe("extractThinking", () => {
	it("extracts thoughts and separates clean content", async () => {
		const { extractThinking } = await import("../src/core/chat/agent");
		const raw = "<think>Analyzing user query\nChecking journal...</think>Here is your summary.";
		const { thoughts, content } = extractThinking(raw);
		expect(thoughts).toHaveLength(1);
		expect(thoughts[0]).toBe("Analyzing user query\nChecking journal...");
		expect(content).toBe("Here is your summary.");
	});

	it("handles multiple or empty thoughts", async () => {
		const { extractThinking } = await import("../src/core/chat/agent");
		const raw = "<thought>First thought</thought>Middle text<think>Second thought</think>End.";
		const { thoughts, content } = extractThinking(raw);
		expect(thoughts).toEqual(["First thought", "Second thought"]);
		expect(content).toBe("Middle textEnd.");
	});
});
