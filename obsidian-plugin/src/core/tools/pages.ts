/**
 * Pages reading tool using Obsidian's MetadataCache and Vault.
 */
import { App, TFile } from "obsidian";

export function resolveVaultPage(app: App, pageName: string): TFile | null {
	const cleanName = pageName
		.replace(/^\[\[/, "")
		.replace(/\]\]$/, "")
		.split("#")[0]
		.split("|")[0]
		.trim();
	if (!cleanName) return null;

	// 1. Try getFirstLinkpathDest
	const file = app.metadataCache.getFirstLinkpathDest(cleanName, "");
	if (file && file instanceof TFile) return file;

	// 2. Fallback: match basename or relative path
	const markdownFiles = app.vault.getMarkdownFiles();
	const targetNoExt = cleanName.replace(/\.md$/, "");
	const found =
		markdownFiles.find(
			(f) =>
				f.basename === targetNoExt ||
				f.path === cleanName ||
				f.path === `${cleanName}.md` ||
				f.path.endsWith(`/${cleanName}.md`)
		) || null;

	return found instanceof TFile ? found : null;
}

export async function readPages(app: App, pageNames: string[]): Promise<string> {
	if (!pageNames || pageNames.length === 0) {
		return "Error: No page names provided.";
	}

	const outputs: string[] = [];

	for (const rawName of pageNames) {
		const file = resolveVaultPage(app, rawName);
		if (file) {
			const content = await app.vault.cachedRead(file);
			outputs.push(`# ${file.basename}\n${content}`);
		} else {
			outputs.push(`Page '${rawName}' not found in vault.`);
		}
	}

	return outputs.join("\n\n---\n\n");
}
