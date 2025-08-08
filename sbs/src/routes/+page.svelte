<script>
  import { onMount } from 'svelte';
  import Fuse from 'fuse.js';

  let query = '';
  let loading = false;
  let error = '';
  import PageViewer from '$lib/PageViewer.svelte';
  let content = '';
  let path = '';
  let baseName = '';
  let retros = [];
  let activeRetro = 0;
  let pages = [];
  let fuse;
  let suggestions = [];
  let showSuggestions = false;
  let highlighted = -1;
  let listEl;
  let itemRefs = [];

  async function search(evt) {
    evt?.preventDefault();
    error = '';
    content = '';
    path = '';
    if (!query.trim()) return;
    loading = true;
    try {
      const res = await fetch(`/api/page?name=${encodeURIComponent(query.trim())}`);
      const data = await res.json();
      if (!res.ok) {
        error = data?.error || 'Request failed';
        return;
      }
      content = data.content || '';
      path = data.path || '';
      baseName = (data.path || '').split('/').pop()?.replace(/\.md$/, '') || '';
      await loadRetros(baseName);
    } catch (e) {
      error = String(e);
    } finally {
      loading = false;
    }
  }

  async function loadRetros(base) {
    retros = [];
    activeRetro = 0;
    if (!base) return;
    try {
      const res = await fetch(`/api/related?base=${encodeURIComponent(base)}`);
      const data = await res.json();
      if (res.ok && Array.isArray(data.items)) {
        retros = data.items;
      }
    } catch (e) {
      // ignore related errors for now
    }
  }

  onMount(async () => {
    try {
      const res = await fetch('/api/pages');
      const data = await res.json();
      if (res.ok && Array.isArray(data.items)) {
        pages = data.items;
        fuse = new Fuse(pages, {
          keys: ['name', 'path'],
          includeScore: true,
          threshold: 0.35,
          ignoreLocation: true,
          minMatchCharLength: 3
        });
      }
    } catch {
      // ignore suggestion load errors
    }
  });

  $: if (fuse) {
    const q = query.trim();
    if (q.length >= 3) {
      suggestions = fuse.search(q).slice(0, 10).map((r) => r.item);
      showSuggestions = suggestions.length > 0;
      highlighted = suggestions.length ? 0 : -1;
      // reset refs when suggestions change
      itemRefs = new Array(suggestions.length);
      // after next tick, align scroll so highlighted is at top
      queueMicrotask(() => scrollToHighlighted(true));
    } else {
      suggestions = [];
      showSuggestions = false;
      highlighted = -1;
    }
  }

  function handleKeydown(e) {
    if (!showSuggestions || suggestions.length === 0) {
      if (e.key === 'Enter') {
        e.preventDefault();
        search();
      }
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      highlighted = Math.min(highlighted + 1, suggestions.length - 1);
      scrollToHighlighted(true);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      highlighted = Math.max(highlighted - 1, 0);
      scrollToHighlighted(true);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (highlighted >= 0) pickSuggestion(suggestions[highlighted]);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      showSuggestions = false;
    }
  }

  function pickSuggestion(s) {
    if (!s) return;
    query = s.name;
    showSuggestions = false;
    search();
  }

  function scrollToHighlighted(alignTop = false) {
    if (!listEl || highlighted < 0) return;
    const el = itemRefs[highlighted];
    if (!el) return;
    if (alignTop) {
      const top = el.offsetTop - listEl.offsetTop;
      listEl.scrollTop = top;
    } else {
      el.scrollIntoView({ block: 'nearest' });
    }
  }

  // Svelte action to capture per-item refs in the suggestions list
  function captureRef(node, index) {
    itemRefs[index] = node;
    return {
      destroy() {
        if (itemRefs[index] === node) itemRefs[index] = null;
      }
    };
  }
</script>

<main class="min-h-screen bg-slate-50">
  <div class="flex min-h-screen">
    <!-- Sidebar -->
    <aside class="w-80 shrink-0 border-r border-slate-200 bg-white p-4">
      <h1 class="mb-4 text-lg font-semibold text-slate-900">Vault Browser</h1>
      <form on:submit|preventDefault={search} class="space-y-3">
        <label class="block text-sm font-medium text-slate-700" for="page">Page name</label>
        <div class="relative">
          <input
            id="page"
            class="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900 placeholder-slate-400 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            type="text"
            bind:value={query}
            placeholder="e.g. 2025-01-02"
          on:focus={() => (showSuggestions = suggestions.length > 0)}
          on:blur={() => setTimeout(() => (showSuggestions = false), 100)}
          on:keydown={handleKeydown}
          />
          {#if showSuggestions}
            <ul bind:this={listEl} role="listbox" class="absolute z-10 mt-1 max-h-96 w-full overflow-auto rounded-md border border-slate-200 bg-white py-1 text-sm shadow">
              {#each suggestions as s, i}
                <li use:captureRef={i} role="option" aria-selected={i === highlighted}>
                  <button
                    type="button"
                    class="block w-full px-3 py-1.5 text-left hover:bg-slate-50"
                    class:bg-indigo-50={i === highlighted}
                    class:text-indigo-700={i === highlighted}
                    on:mouseenter={() => highlighted = i}
                    on:click={() => pickSuggestion(s)}
                  >
                    <span class="font-medium text-slate-900">{s.name}</span>
                    <span class="ml-2 text-slate-400 text-xs">{s.path}</span>
                  </button>
                </li>
              {/each}
            </ul>
          {/if}
        </div>
        <button
          class="w-full rounded-md bg-indigo-600 px-3 py-2 text-white shadow hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={loading || !query.trim()}
          on:click={search}
          type="button"
        >
          {#if loading}
            Searching…
          {:else}
            Open page
          {/if}
        </button>
        {#if error}
          <p class="text-sm text-red-600">{error}</p>
        {/if}
        {#if path}
          <p class="text-xs text-slate-500 break-all">Found: {path}</p>
        {/if}
      </form>
    </aside>

    <!-- Main content -->
    <section class="flex-1 p-6">
      {#if content}
        {#if retros.length > 0}
          <div class="flex gap-6">
            <div class="w-1/2 min-w-0">
              <PageViewer raw={content} on:wikilink={(e) => { query = e.detail.page; search(); }} />
            </div>
            <div class="w-1/2 min-w-0">
              <div class="border-b border-slate-200 mb-4 flex flex-wrap gap-2">
                {#each retros as r, i}
                  <button
                    class="rounded-t px-3 py-1.5 text-sm border-b-2 -mb-px"
                    class:border-b-indigo-600={i === activeRetro}
                    class:text-indigo-700={i === activeRetro}
                    class:text-slate-600={i !== activeRetro}
                    on:click={() => activeRetro = i}
                  >
                    {r.name}
                  </button>
                {/each}
              </div>
              <div>
                <PageViewer raw={retros[activeRetro]?.content || ''} on:wikilink={(e) => { query = e.detail.page; search(); }} />
              </div>
            </div>
          </div>
        {:else}
          <PageViewer raw={content} on:wikilink={(e) => { query = e.detail.page; search(); }} />
        {/if}
      {:else}
        <div class="text-slate-500">Enter a page name in the sidebar to view its contents.</div>
      {/if}
    </section>
  </div>
</main>
