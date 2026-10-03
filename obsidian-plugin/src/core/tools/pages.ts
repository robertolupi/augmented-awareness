/**
 * Pages reading tool using Obsidian's MetadataCache and Vault.
 */
import { App, TFile } from "obsidian";

export async function readPages(app: App, pageNames: string[]): Promise<string> {
	if (!pageNames || pageNames.length === 0) {
		return "Error: No page names provided.";
	}

	const outputs: string[] = [];
	const markdownFiles = app.vault.getMarkdownFiles();

	for (const rawName of pageNames) {
		const cleanName = rawName.replace(/^\[\[/, "").replace(/\]\]$/, "").trim();
		if (!cleanName) continue;

		// 1. Try getFirstLinkpathDest
		let file = app.metadataCache.getFirstLinkpathDest(cleanName, "");

		// 2. Fallback: match basename or relative path
		if (!file) {
			const targetNoExt = cleanName.replace(/\.md$/, "");
			file =
				markdownFiles.find(
					(f) =>
						f.basename === targetNoExt ||
						f.path === cleanName ||
						f.path === `${cleanName}.md` ||
						f.path.endsWith(`/${cleanName}.md`)
				) || null;
		}

		if (file && file instanceof TFile) {
			const content = await app.vault.cachedRead(file);
			outputs.push(`# ${file.basename}\n${content}`);
		} else {
			outputs.push(`Page '${cleanName}' not found in vault.`);
		}
	}

	return outputs.join("\n\n---\n\n");
}
