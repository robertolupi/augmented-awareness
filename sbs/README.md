SBS — SvelteKit + Tailwind starter

Quick start

- Install dependencies: `npm install` (or `pnpm install` / `yarn install`).
- Start dev server: `npm run dev` then open the URL printed (usually http://localhost:5173).
- Build for production: `npm run build` then `npm run preview`.

Notes

- Tailwind CSS is wired via PostCSS. Global styles live in `src/app.css` and are imported in `src/routes/+layout.svelte`.
- Main route is `src/routes/+page.svelte` showing a simple Tailwind-styled Hello World.
- Config files:
  - `svelte.config.js` with `@sveltejs/adapter-auto`
  - `vite.config.js` using the SvelteKit Vite plugin
  - `postcss.config.cjs` and `tailwind.config.cjs` for Tailwind

