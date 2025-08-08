import { env } from '$env/dynamic/private';
import { promises as fs } from 'node:fs';
import path from 'node:path';

export async function GET({ url }) {
  const base = env.VAULT_PATH;
  if (!base) {
    return new Response(JSON.stringify({ error: 'VAULT_PATH is not set in the environment' }), { status: 500 });
  }

  const name = url.searchParams.get('base');
  if (!name) {
    return new Response(JSON.stringify({ error: 'Missing required query param `base`' }), { status: 400 });
  }

  try {
    const files = await findRetros(base, name);
    const items = await Promise.all(
      files.map(async (p) => ({
        path: p,
        name: path.basename(p),
        content: await fs.readFile(p, 'utf-8')
      }))
    );
    return new Response(JSON.stringify({ items }), { headers: { 'content-type': 'application/json' } });
  } catch (err) {
    return new Response(JSON.stringify({ error: 'Internal error', details: String(err) }), { status: 500 });
  }
}

async function findRetros(root, baseName) {
  const retrosBase = computeRetrosBase(baseName);
  const re = new RegExp(`^${escapeRegExp(retrosBase)}(?:\\.(\\d+))?\\.md$`);
  const matches = [];
  const queue = [root];

  while (queue.length) {
    const dir = queue.shift();
    let entries;
    try {
      entries = await fs.readdir(dir, { withFileTypes: true });
    } catch {
      continue;
    }
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name === '.git' || entry.name === 'node_modules' || entry.name.startsWith('.')) continue;
        queue.push(full);
      } else if (entry.isFile()) {
        const m = entry.name.match(re);
        if (m) {
          const idx = m[1] ? parseInt(m[1], 10) : 0;
          matches.push({ full, idx });
        }
      }
    }
  }

  matches.sort((a, b) => a.idx - b.idx || a.full.localeCompare(b.full));
  return matches.map((m) => m.full);
}

function escapeRegExp(s) {
  return String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function computeRetrosBase(baseName) {
  // Special case: Yearly pages use YYYYY (e.g., Y2025) but retros are rYYYY (e.g., r2025)
  const m = /^Y(\d{4})$/.exec(baseName);
  if (m) return `r${m[1]}`;
  return `r${baseName}`;
}
