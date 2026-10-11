// The site of wand125/square-packing: static pages for GitHub Pages, written in Astro and MDX with Preact components.
// URLs stay as before (results.html, rect-regions.html, …): build.format 'file'. Mathematics is typeset at build time by KaTeX.
import { defineConfig } from 'astro/config';
import {interactiveData} from './scripts/interactive-data.mjs';
import mdx from '@astrojs/mdx';
import preact from '@astrojs/preact';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

export default defineConfig({
  site: 'https://wand125.github.io',
  base: '/square-packing',
  build: { format: 'file' },
  trailingSlash: 'never',
  integrations: [mdx(), preact(), interactiveData()],
  markdown: { remarkPlugins: [remarkMath], rehypePlugins: [rehypeKatex] },
});
