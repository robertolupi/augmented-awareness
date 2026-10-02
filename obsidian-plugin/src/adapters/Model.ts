import { App } from "obsidian";

/**
 * Model adapter boundary (doc/obsidian-plugin-design.md, "Proposed modules"
 * and "Provider boundary: decision 1"). The core talks to this interface so
 * prompt and planner tests do not depend on the AI Providers plugin.
 */
export interface ModelAdapter {
	generate(system: string, user: string): Promise<string>;
}

export class ModelError extends Error {
	constructor(
		message: string,
		readonly code:
			| "ai_providers_missing"
			| "ai_providers_incompatible"
			| "provider_not_found"
			| "generation_failed"
	) {
		super(message);
		this.name = "ModelError";
	}
}

/**
 * Minimal shape of the AI Providers service, verified against the installed
 * AI Providers 1.10.0 bundle and Local GPT's usage of it. The service is not
 * an import: AI Providers assigns it to the `app.aiProviders` global and
 * fires an `ai-providers-ready` workspace event once loaded.
 */
export interface AIProviderEntry {
	id: string;
	model: string;
	name?: string;
	type?: string;
	url?: string;
	availableModels?: string[];
}

export interface AIProvidersService {
	version: number;
	providers: AIProviderEntry[];
	checkCompatibility(requiredVersion: number): void;
	execute(params: {
		provider: AIProviderEntry;
		messages?: { role: string; content: string }[];
		model?: string;
		abortController?: AbortController;
		onProgress?: (chunk: string, accumulatedText: string) => void;
	}): Promise<string>;
}

const REQUIRED_SERVICE_VERSION = 4;
const READY_EVENT = "ai-providers-ready";
const READY_TIMEOUT_MS = 5000;

type AppWithAIProviders = App & { aiProviders?: AIProvidersService };

/**
 * Read the service from the `app.aiProviders` global, waiting once for the
 * `ai-providers-ready` workspace event if AI Providers has not loaded yet.
 */
async function resolveService(
	app: AppWithAIProviders
): Promise<AIProvidersService> {
	if (app.aiProviders) {
		return app.aiProviders;
	}
	return new Promise<AIProvidersService>((resolve, reject) => {
		const timer = setTimeout(() => {
			offWorkspaceEvent(app, READY_EVENT, onReady);
			reject(
				new ModelError(
					"AI Providers plugin is not available. Install and enable it, then configure a provider.",
					"ai_providers_missing"
				)
			);
		}, READY_TIMEOUT_MS);
		const onReady = () => {
			clearTimeout(timer);
			const service = (app as AppWithAIProviders).aiProviders;
			if (service) {
				resolve(service);
			} else {
				reject(
					new ModelError(
						"AI Providers signalled readiness but exposed no service.",
						"ai_providers_missing"
					)
				);
			}
		};
		onWorkspaceEvent(app, READY_EVENT, onReady);
	});
}

// `ai-providers-ready` is a custom workspace event fired by the AI Providers
// plugin; Obsidian's typed overloads only cover built-in event names.
function onWorkspaceEvent(app: App, name: string, callback: () => void): void {
	(
		app.workspace.on as unknown as (
			name: string,
			callback: () => void
		) => void
	)(name, callback);
}

function offWorkspaceEvent(app: App, name: string, callback: () => void): void {
	(
		app.workspace.off as unknown as (
			name: string,
			callback: () => void
		) => void
	)(name, callback);
}

/**
 * Production adapter backed by the AI Providers plugin. The service is
 * resolved at request time so provider changes in AI Providers settings are
 * picked up without reloading this plugin.
 */
export class AIProvidersModelAdapter implements ModelAdapter {
	constructor(
		private readonly app: App,
		private readonly providerId: string,
		private readonly model: string
	) {}

	async generate(system: string, user: string): Promise<string> {
		const service = await resolveService(this.app as AppWithAIProviders);
		try {
			service.checkCompatibility(REQUIRED_SERVICE_VERSION);
		} catch (err) {
			throw new ModelError(
				`AI Providers service is incompatible (needs service API v${REQUIRED_SERVICE_VERSION}): ${
					err instanceof Error ? err.message : String(err)
				}`,
				"ai_providers_incompatible"
			);
		}
		const provider = service.providers.find(
			(p) => p.id === this.providerId
		);
		if (!provider) {
			throw new ModelError(
				`Provider "${this.providerId}" not found in AI Providers. Configure it in the AI Providers settings and select its ID in AWW Retrospectives settings.`,
				"provider_not_found"
			);
		}
		try {
			// Passing an AbortController (even without streaming) selects the
			// modern SDK path, where execute() resolves to the full text
			// instead of the deprecated chainable chunk handler.
			return await service.execute({
				provider,
				model: this.model || undefined,
				messages: [
					{ role: "system", content: system },
					{ role: "user", content: user },
				],
				abortController: new AbortController(),
			});
		} catch (err) {
			if (err instanceof ModelError) {
				throw err;
			}
			throw new ModelError(
				`Generation failed: ${
					err instanceof Error ? err.message : String(err)
				}`,
				"generation_failed"
			);
		}
	}
}
