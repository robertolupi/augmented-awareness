import { describe, it, expect } from 'vitest';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseFrontmatterAndMarkdown } from './parse.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Path to the repository root test vault from the sbs package
const vaultFile = path.resolve(__dirname, '../../..', 'test_vault/journal/2025/04/2025-04-01.md');

describe('parseFrontmatterAndMarkdown', () => {
  it('parses YAML frontmatter and markdown content', async () => {
    const raw = await readFile(vaultFile, 'utf-8');
    const { frontmatter, html } = parseFrontmatterAndMarkdown(raw);

    // frontmatter
    expect(frontmatter).toBeTypeOf('object');
    expect(frontmatter.stress).toBe(5);

    // markdown rendered
    expect(html).toContain('A journal page with frontmatter');
    // should include headings in sanitized output
    expect(html).toMatch(/<h1[^>]*>\s*2025-04-01\s*<\/h1>/);

    // should not include the YAML fence or keys in the rendered body
    expect(html).not.toContain('---');
    expect(html).not.toContain('stress: 5');
  });

  it('parses with Windows CRLF line endings', async () => {
    const raw = await readFile(vaultFile, 'utf-8');
    const crlf = raw.replaceAll('\n', '\r\n');
    const { frontmatter, html } = parseFrontmatterAndMarkdown(crlf);
    expect(frontmatter.stress).toBe(5);
    expect(html).toMatch(/<h1[^>]*>\s*2025-04-01\s*<\/h1>/);
  });

  it('converts Obsidian wiki-links to anchors with data attributes', async () => {
    const raw = await readFile(vaultFile, 'utf-8');
    const { html } = parseFrontmatterAndMarkdown(raw);
    expect(html).toMatch(/<a[^>]*data-wikilink="2025-03-30"[^>]*data-anchor="Schedule"[^>]*>\s*2025-03-30#Schedule\s*<\/a>/);
  });
});
