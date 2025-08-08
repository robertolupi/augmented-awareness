<script>
  let query = '';
  let loading = false;
  let error = '';
  import PageViewer from '$lib/PageViewer.svelte';
  let content = '';
  let path = '';
  let baseName = '';
  let retros = [];
  let activeRetro = 0;

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
</script>

<main class="min-h-screen bg-slate-50">
  <div class="flex min-h-screen">
    <!-- Sidebar -->
    <aside class="w-80 shrink-0 border-r border-slate-200 bg-white p-4">
      <h1 class="mb-4 text-lg font-semibold text-slate-900">Vault Browser</h1>
      <form on:submit|preventDefault={search} class="space-y-3">
        <label class="block text-sm font-medium text-slate-700" for="page">Page name</label>
        <input
          id="page"
          class="w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900 placeholder-slate-400 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          type="text"
          bind:value={query}
          placeholder="e.g. 2025-01-02"
        />
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
