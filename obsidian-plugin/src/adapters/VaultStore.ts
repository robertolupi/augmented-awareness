import { App, TFile, normalizePath } from "obsidian";

export interface VaultStore {
	exists(path: string): Promise<boolean>;
	read(path: string): Promise<string>;
	write(path: string, content: string): Promise<void>;
	rename(fromPath: string, toPath: string): Promise<void>;
	ensureFolder(dirPath: string): Promise<void>;
	mtime(path: string): Promise<number>;
}


export class ObsidianVaultStore implements VaultStore {
	constructor(private readonly app: App) {}

	async exists(path: string): Promise<boolean> {
		return Boolean(
			this.app.vault.getAbstractFileByPath(normalizePath(path))
		);
	}

	async read(path: string): Promise<string> {
		const file = this.app.vault.getAbstractFileByPath(normalizePath(path));
		if (file instanceof TFile) {
			return await this.app.vault.read(file);
		}
		throw new Error(`File not found: ${path}`);
	}

	async ensureFolder(dirPath: string): Promise<void> {
		const normalized = normalizePath(dirPath);
		if (!this.app.vault.getAbstractFileByPath(normalized)) {
			await this.app.vault.createFolder(normalized);
		}
	}

	async rename(fromPath: string, toPath: string): Promise<void> {
		const file = this.app.vault.getAbstractFileByPath(
			normalizePath(fromPath)
		);
		if (file instanceof TFile) {
			await this.app.vault.rename(file, normalizePath(toPath));
		}
	}

	async write(path: string, content: string): Promise<void> {
		const normalized = normalizePath(path);
		const lastSlash = normalized.lastIndexOf("/");
		if (lastSlash > 0) {
			const parent = normalized.slice(0, lastSlash);
			await this.ensureFolder(parent);
		}
		const existing = this.app.vault.getAbstractFileByPath(normalized);
		if (existing instanceof TFile) {
			await this.app.vault.modify(existing, content);
		} else {
			await this.app.vault.create(normalized, content);
		}
	}

	async mtime(path: string): Promise<number> {
		const file = this.app.vault.getAbstractFileByPath(
			normalizePath(path)
		);
		if (file instanceof TFile) {
			return file.stat.mtime;
		}
		return 0;
	}
}

