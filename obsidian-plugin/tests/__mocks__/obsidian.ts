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

export class TFile {}
export function normalizePath(path: string): string {
	return path;
}
