/**
 * Chat agent executing the multi-step tool-calling loop using AI Providers toolsExecute.
 */
import { App } from "obsidian";
import type { AIProviderEntry, AIProvidersService } from "../../adapters/Model";
import { CHAT_TOOLS, executeTool } from "../tools/registry";
import { prepareOutput } from "../output";

export interface ChatMessage {
	id: string;
	role: "user" | "assistant" | "system" | "tool";
	content: string;
	timestamp: number;
	tool_calls?: any[];
	tool_call_id?: string;
	tool_name?: string;
	stopped?: boolean;
}

export class ChatCancelledError extends Error {
	generatedMessages: ChatMessage[];
	partialContent: string;

	constructor(
		message = "Chat generation cancelled.",
		generatedMessages: ChatMessage[] = [],
		partialContent = ""
	) {
		super(message);
		this.name = "ChatCancelledError";
		this.generatedMessages = generatedMessages;
		this.partialContent = partialContent;
	}
}

export interface RunChatAgentOptions {
	app: App;
	provider: AIProviderEntry;
	model?: string;
	systemPrompt: string;
	messages: ChatMessage[];
	journalDir?: string;
	retroDir?: string;
	abortController: AbortController;
	onProgress?: (chunk: string, accumulated: string) => void;
	onToolCallStart?: (toolName: string, args: Record<string, any>) => void;
	onToolCallEnd?: (toolName: string, result: string) => void;
}

export interface ChatAgentResult {
	finalContent: string;
	generatedMessages: ChatMessage[];
}

export async function runChatAgent(
	options: RunChatAgentOptions
): Promise<ChatAgentResult> {
	const {
		app,
		provider,
		model,
		systemPrompt,
		messages: initialMessages,
		journalDir,
		retroDir,
		abortController,
		onProgress,
		onToolCallStart,
		onToolCallEnd,
	} = options;

	const aiProviders = (app as any).aiProviders as AIProvidersService | undefined;
	if (!aiProviders) {
		throw new Error(
			"AI Providers plugin is missing. Please ensure the AI Providers plugin is installed and enabled."
		);
	}

	// Build OpenAI format messages
	const openAiMessages: any[] = [
		{ role: "system", content: systemPrompt },
	];

	for (const msg of initialMessages) {
		if (msg.role === "user") {
			openAiMessages.push({ role: "user", content: msg.content });
		} else if (msg.role === "assistant") {
			const m: any = { role: "assistant", content: msg.content || null };
			if (msg.tool_calls && msg.tool_calls.length > 0) {
				m.tool_calls = msg.tool_calls;
			}
			openAiMessages.push(m);
		} else if (msg.role === "tool") {
			openAiMessages.push({
				role: "tool",
				tool_call_id: msg.tool_call_id,
				content: msg.content,
			});
		} else if (msg.role === "system") {
			openAiMessages.push({
				role: "system",
				content: msg.content,
			});
		}
	}

	const generatedMessages: ChatMessage[] = [];
	let step = 0;
	const maxSteps = 8;
	let finalContent = "";
	let latestAccumulated = "";

	while (step < maxSteps) {
		step++;

		if (abortController.signal.aborted) {
			throw new ChatCancelledError(
				"Chat generation cancelled.",
				generatedMessages,
				latestAccumulated
			);
		}

		// Execute with tools
		let response: any;
		try {
			if (typeof (aiProviders as any).toolsExecute === "function") {
				response = await (aiProviders as any).toolsExecute({
					provider,
					model: model || provider.model,
					messages: openAiMessages,
					tools: CHAT_TOOLS,
					abortController,
					onProgress: (chunk: string, accumulated: string) => {
						latestAccumulated = accumulated;
						if (onProgress) {
							onProgress(chunk, accumulated);
						}
					},
				});
			} else {
				// Fallback to standard execute if toolsExecute is absent
				const text = await aiProviders.execute({
					provider,
					model: model || provider.model,
					messages: openAiMessages,
					abortController,
					onProgress: (chunk: string, accumulated: string) => {
						latestAccumulated = accumulated;
						if (onProgress) {
							onProgress(chunk, accumulated);
						}
					},
				});
				response = { role: "assistant", content: text };
			}
		} catch (err: any) {
			if (
				abortController.signal.aborted ||
				err.message === "Aborted" ||
				err.name === "AbortError"
			) {
				throw new ChatCancelledError(
					"Chat generation cancelled.",
					generatedMessages,
					latestAccumulated
				);
			}
			throw err;
		}

		const hasToolCalls =
			response &&
			Array.isArray(response.tool_calls) &&
			response.tool_calls.length > 0;

		if (hasToolCalls) {
			// Assistant asked to call tools
			const assistantContent = response.content || "";
			const assistantMsg: ChatMessage = {
				id: `asst-${Date.now()}-${step}`,
				role: "assistant",
				content: assistantContent,
				timestamp: Date.now(),
				tool_calls: response.tool_calls,
			};
			generatedMessages.push(assistantMsg);
			openAiMessages.push({
				role: "assistant",
				content: assistantContent || null,
				tool_calls: response.tool_calls,
			});

			for (const call of response.tool_calls) {
				if (abortController.signal.aborted) {
					throw new ChatCancelledError(
						"Chat generation cancelled.",
						generatedMessages,
						latestAccumulated
					);
				}

				const toolName = call.function?.name || "";
				let args: Record<string, any> = {};
				try {
					args = JSON.parse(call.function?.arguments || "{}");
				} catch {
					args = {};
				}

				if (onToolCallStart) {
					onToolCallStart(toolName, args);
				}

				const result = await executeTool(toolName, args, {
					app,
					journalDir,
					retroDir,
				});

				if (abortController.signal.aborted) {
					throw new ChatCancelledError(
						"Chat generation cancelled.",
						generatedMessages,
						latestAccumulated
					);
				}

				if (onToolCallEnd) {
					onToolCallEnd(toolName, result);
				}

				const toolMsg: ChatMessage = {
					id: `tool-${Date.now()}-${call.id}`,
					role: "tool",
					content: result,
					timestamp: Date.now(),
					tool_call_id: call.id,
					tool_name: toolName,
				};
				generatedMessages.push(toolMsg);
				openAiMessages.push({
					role: "tool",
					tool_call_id: call.id,
					content: result,
				});
			}

			// Continue loop to send tool results back to model
			continue;
		}

		// Final response received
		const rawContent = response.content || "";
		finalContent = rawContent;

		const finalMsg: ChatMessage = {
			id: `asst-${Date.now()}-${step}`,
			role: "assistant",
			content: rawContent,
			timestamp: Date.now(),
		};
		generatedMessages.push(finalMsg);
		break;
	}

	return {
		finalContent,
		generatedMessages,
	};
}

export function extractThinking(text: string): {
	thoughts: string[];
	content: string;
} {
	const thoughts: string[] = [];
	const THINK_EXTRACT_RE =
		/<(?:think|thought)\b[^>]*>([\s\S]*?)<\/(?:think|thought)>/gi;
	let m: RegExpExecArray | null;
	while ((m = THINK_EXTRACT_RE.exec(text)) !== null) {
		const thought = m[1].trim();
		if (thought) {
			thoughts.push(thought);
		}
	}
	const content = text.replace(THINK_EXTRACT_RE, "").trim();
	return { thoughts, content };
}
