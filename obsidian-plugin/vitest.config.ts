import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { defineConfig } from "vitest/config";

// Import .md files as text in tests, matching the esbuild "text" loader used
// for the plugin bundle.
export default defineConfig({
	resolve: {
		alias: {
			obsidian: fileURLToPath(
				new URL("./tests/__mocks__/obsidian.ts", import.meta.url)
			),
		},
	},
	plugins: [
		{
			name: "md-text",
			transform(_code, id) {
				if (id.endsWith(".md")) {
					return {
						code: `export default ${JSON.stringify(
							readFileSync(id, "utf8")
						)};`,
					};
				}
			},
		},
	],
});
