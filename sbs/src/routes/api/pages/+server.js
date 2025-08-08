import { env } from '$env/dynamic/private';
import { promises as fs } from 'node:fs';
import path from 'node:path';

export async function GET() {
  const base = env.VAULT_PATH;
  if (!base) {
    return new Response(JSON.stringify({ error: 'VAULT_PATH is not set in the environment' }), { status: 500 });
  }

  try {
    const items = await listMarkdownFiles(base);
    return new Response(JSON.stringify({ items }), { headers: { 'content-type': 'application/json' } });
  } catch (err) {
    return new Response(JSON.stringify({ error: 'Internal error', details: String(err) }), { status: 500 });
  }
}

async function listMarkdownFiles(root) {
  const out = [];
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
      } else if (entry.isFile() && entry.name.toLowerCase().endsWith('.md')) {
        out.push({ path: full, name: entry.name.replace(/\.md$/i, '') });
      }
    }
  }
  return out;
}

