// Minimal runtime stub for the types-only "obsidian" package, so vitest can
// import modules that reference Obsidian API classes. Only the pieces used at
// module level need to exist as constructors.
export class Notice {
	constructor(_message?: string) {}
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
}
export class TFile {}
export function normalizePath(path: string): string {
	return path;
}
