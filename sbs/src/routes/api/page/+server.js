import { env } from '$env/dynamic/private';
import { promises as fs } from 'node:fs';
import path from 'node:path';

/**
 * GET /api/page?name=foo
 * Looks for `foo.md` anywhere under VAULT_PATH and returns its content.
 */
export async function GET({ url }) {
  const name = url.searchParams.get('name');
  if (!name) {
    return new Response(JSON.stringify({ error: 'Missing required query param `name`' }), { status: 400 });
  }

  const base = env.VAULT_PATH;
  if (!base) {
    return new Response(JSON.stringify({ error: 'VAULT_PATH is not set in the environment' }), { status: 500 });
  }

  const target = name.endsWith('.md') ? name : `${name}.md`;

  try {
    const foundPath = await findFileRecursive(base, target);
    if (!foundPath) {
      return new Response(JSON.stringify({ error: `Page not found: ${target}` }), { status: 404 });
    }

    const content = await fs.readFile(foundPath, 'utf-8');
    return new Response(
      JSON.stringify({ path: foundPath, name: path.basename(foundPath), content }),
      { headers: { 'content-type': 'application/json' } }
    );
  } catch (err) {
    return new Response(JSON.stringify({ error: 'Internal error', details: String(err) }), { status: 500 });
  }
}

async function findFileRecursive(root, filename) {
  const queue = [root];
  while (queue.length) {
    const dir = queue.shift();
    let entries;
    try {
      entries = await fs.readdir(dir, { withFileTypes: true });
    } catch {
      continue; // skip unreadable directories
    }

    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        // Skip common heavy or irrelevant directories
        if (entry.name === '.git' || entry.name === 'node_modules' || entry.name.startsWith('.')) continue;
        queue.push(full);
      } else if (entry.isFile() && entry.name === filename) {
        return full;
      }
    }
  }
  return null;
}

