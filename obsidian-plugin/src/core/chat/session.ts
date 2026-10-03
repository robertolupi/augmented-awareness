/**
 * Chat session management and vault export matching the Streamlit implementation.
 */
import { App, TFile, moment, normalizePath } from "obsidian";
import type { ChatMessage } from "./agent";

export interface ChatSession {
	id: string;
	title: string;
	createdAt: number;
	updatedAt: number;
	providerId?: string;
	model?: string;
	messages: ChatMessage[];
	contextNotePath?: string;
}

export function createNewSession(
	title = "New Chat",
	providerId = "",
	model = ""
): ChatSession {
	const now = Date.now();
	return {
		id: `chat-${now}-${Math.random().toString(36).slice(2, 7)}`,
		title,
		createdAt: now,
		updatedAt: now,
		providerId,
		model,
		messages: [],
	};
}

const THINK_RE = /<(?:think|thought)\b[^>]*>[\s\S]*?<\/(?:think|thought)>/gi;

/**
 * Format chat history as Markdown matching the Streamlit implementation in pages/chat.py.
 */
export function formatChatMarkdown(session: ChatSession): string {
	const dateStr = moment(session.createdAt).format("YYYY-MM-DD HH:mm");
	const lines: string[] = [
		`# ${session.title}\n`,
		`*Date: ${dateStr}${session.model ? ` | Model: \`${session.model}\`` : ""}*\n`,
	];

	for (const msg of session.messages) {
		if (msg.role === "user") {
			lines.push(`### User\n${msg.content}\n`);
		} else if (msg.role === "assistant") {
			// Skip intermediate tool-calling turns
			if (msg.tool_calls && msg.tool_calls.length > 0) {
				continue;
			}
			const cleaned = (msg.content || "").replace(THINK_RE, "").trim();
			if (cleaned) {
				lines.push(
					`### AI\n${cleaned}${msg.stopped ? "\n\n*(Generation stopped by user)*" : ""}\n`
				);
			} else if (msg.stopped) {
				lines.push(`### AI\n*(Generation stopped by user)*\n`);
			}
		}
	}

	return lines.join("\n").trim();
}

/**
 * Save chat session to vault under Chats/YYYY-MM-DD <title>.md, matching pages/chat.py.
 */
export async function saveChatToVault(
	app: App,
	session: ChatSession,
	folder = "Chats"
): Promise<{ file: TFile; path: string }> {
	// Ensure Chats folder exists
	const normalizedFolder = normalizePath(folder);
	const existingFolder = app.vault.getAbstractFileByPath(normalizedFolder);
	if (!existingFolder) {
		await app.vault.createFolder(normalizedFolder);
	}

	const today = moment().format("YYYY-MM-DD");
	const safeTitle = (session.title || "Chat")
		.replace(/[\\/:*?"<>|#^\[\]]/g, "-")
		.trim();
	const filename = `${today} ${safeTitle}.md`;
	const notePath = normalizePath(`${normalizedFolder}/${filename}`);
	const markdownContent = formatChatMarkdown(session);

	const existingFile = app.vault.getAbstractFileByPath(notePath);
	let file: TFile;

	if (existingFile && existingFile instanceof TFile) {
		await app.vault.modify(existingFile, markdownContent);
		file = existingFile;
	} else {
		file = await app.vault.create(notePath, markdownContent);
	}

	return { file, path: notePath };
}
