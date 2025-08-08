import { marked } from 'marked';
import sanitizeHtml from 'sanitize-html';
import YAML from 'yaml';

export function parseFrontmatterAndMarkdown(text) {
  const input = text ?? '';
  // Support BOM at start
  const startsWithBOM = input.charCodeAt(0) === 0xfeff;
  const start = startsWithBOM ? 1 : 0;

  let frontmatter = {};
  let body = input;

  // Detect frontmatter only if file starts with --- followed by newline (per spec)
  const headerPattern = /^(?:\uFEFF)?---\r?\n([\s\S]*?)\r?\n---\r?\n?/;
  const m = input.slice(start).match(headerPattern);
  if (m && (startsWithBOM || input.startsWith('---'))) {
    const fullMatch = m[0];
    const yamlText = m[1];
    const offset = start + fullMatch.length;
    body = input.slice(offset);
    try {
      const parsed = YAML.parse(yamlText) ?? {};
      if (parsed && typeof parsed === 'object') frontmatter = parsed;
    } catch {
      frontmatter = {};
      // keep body as is
    }
  }

  const rendered = marked.parse(transformWikiLinks(body ?? ''));
  const clean = sanitizeHtml(rendered, {
    allowedTags: sanitizeHtml.defaults.allowedTags.concat(['img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'code', 'pre', 'table', 'thead', 'tbody', 'tr', 'th', 'td']),
    allowedAttributes: {
      ...sanitizeHtml.defaults.allowedAttributes,
      img: ['src', 'alt', 'title'],
      a: ['href', 'name', 'target', 'rel', 'data-wikilink', 'data-anchor']
    },
    allowedSchemes: ['http', 'https', 'mailto']
  });
  return { frontmatter, html: clean };
}

function transformWikiLinks(md) {
  if (!md || md.indexOf('[[') === -1) return md;
  return md.replace(/\[\[([^\]]+)\]\]/g, (_m, inner) => {
    const raw = String(inner);
    const [targetPart, aliasPart] = raw.split('|');
    let page = targetPart;
    let anchor = '';
    const hashIdx = targetPart.indexOf('#');
    if (hashIdx !== -1) {
      page = targetPart.slice(0, hashIdx);
      anchor = targetPart.slice(hashIdx + 1);
    }
    const visible = typeof aliasPart === 'string' ? aliasPart : raw;
    const attrs = [
      `href="#"`,
      `data-wikilink="${escapeAttr(page)}"`
    ];
    if (anchor) attrs.push(`data-anchor="${escapeAttr(anchor)}"`);
    return `<a ${attrs.join(' ')}>${escapeHtml(visible)}</a>`;
  });
}

function escapeAttr(s) {
  return String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
