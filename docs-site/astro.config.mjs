import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://typact-docs.chatgpt-sites.com',
  output: 'static',
  markdown: {
    shikiConfig: { theme: 'github-dark-default' },
  },
});
