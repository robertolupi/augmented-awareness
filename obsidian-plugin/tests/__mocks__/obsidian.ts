// Minimal runtime stub for the types-only "obsidian" package, so vitest can
// import modules that reference Obsidian API classes. Only the pieces used at
// module level need to exist as constructors.
import moment from "moment";
export { moment };

export class Notice {
	constructor(_message?: unknown, _duration?: number) {}
	hide(): void {}
}

export class Plugin {}
export class PluginSettingTab {}
export class Setting {
	setName(_name: string): this {
		return this;
	}
	setDesc(_desc: string): this {
		return this;
	}
	addText(_cb: (text: unknown) => void): this {
		return this;
	}
	addTextArea(_cb: (text: unknown) => void): this {
		return this;
	}
	addDropdown(_cb: (dropdown: unknown) => void): this {
		return this;
	}
	addToggle(_cb: (toggle: unknown) => void): this {
		return this;
	}
	addButton(_cb: (btn: unknown) => void): this {
		return this;
	}
}
export class Modal {
	contentEl: HTMLElement;
	titleEl: HTMLElement;
	constructor(public app: unknown) {
		this.contentEl = {} as HTMLElement;
		this.titleEl = {} as HTMLElement;
	}
	open(): void {}
	close(): void {}
	onOpen(): void {}
	onClose(): void {}
}

export class TFile {
	path: string = "";
	basename: string = "";
	extension: string = "md";
	constructor(path: string = "", basename: string = "") {
		this.path = path;
		this.basename = basename;
	}
}

export function normalizePath(path: string): string {
	return path;
}

export function prepareSimpleSearch(
	query: string
): (text: string) => { score: number; matches: [number, number][] } | null {
	const words = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
	return (text: string) => {
		if (words.length === 0) return null;
		const lower = text.toLowerCase();
		const matches: [number, number][] = [];
		let score = 0;
		for (const w of words) {
			const idx = lower.indexOf(w);
			if (idx === -1) return null; // all words must match in simple search
			matches.push([idx, idx + w.length]);
			score += 5;
		}
		return { score, matches };
	};
}

export class ItemView {
	contentEl: HTMLElement;
	containerEl: HTMLElement;
	constructor(public leaf: any) {
		this.contentEl = {
			empty: () => {},
			createEl: () => ({} as any),
			createDiv: () => ({} as any),
			appendChild: () => {},
		} as any;
		this.containerEl = this.contentEl;
	}
	addAction(_icon: string, _title: string, _cb: any) {}
}

export class WorkspaceLeaf {}

export class MarkdownRenderer {
	static async render(
		_app: any,
		markdown: string,
		el: HTMLElement,
		_sourcePath: string,
		_comp: any
	): Promise<void> {
		if (el) (el as any).textContent = markdown;
	}
}
