<script>
  import { parseFrontmatterAndMarkdown } from '$lib/parse.js';
  import { createEventDispatcher } from 'svelte';

  export let raw = '';

  let frontmatter = {};
  let html = '';
  let open = false; // collapsed by default
  const dispatch = createEventDispatcher();

  $: ({ frontmatter, html } = parseFrontmatterAndMarkdown(raw));
</script>

<div class="space-y-6">
  <details class="rounded border border-slate-200 bg-white shadow-sm" bind:open>
    <summary class="cursor-pointer select-none px-4 py-2 text-sm font-medium text-slate-700 flex items-center gap-2">
      <span>Frontmatter</span>
      {#if Object.keys(frontmatter).length > 0}
        <span class="inline-flex items-center rounded bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700">
          {Object.keys(frontmatter).length}
        </span>
      {/if}
    </summary>
    <div class="px-4 pb-4">
      {#if Object.keys(frontmatter).length > 0}
        <dl class="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
          {#each Object.entries(frontmatter) as [key, value]}
            <div>
              <dt class="text-xs uppercase tracking-wide text-slate-500">{key}</dt>
              <dd class="text-sm text-slate-900 break-words">
                {typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean'
                  ? String(value)
                  : JSON.stringify(value, null, 2)}
              </dd>
            </div>
          {/each}
        </dl>
      {:else}
        <p class="text-sm text-slate-500">No frontmatter found.</p>
      {/if}
    </div>
  </details>

  <article class="prose prose-slate max-w-none" on:click={(e) => {
    const a = e.target.closest('a[data-wikilink]');
    if (a) {
      e.preventDefault();
      const page = a.getAttribute('data-wikilink');
      const anchor = a.getAttribute('data-anchor') || '';
      dispatch('wikilink', { page, anchor });
    }
  }}>
    {@html html}
  </article>
</div>
