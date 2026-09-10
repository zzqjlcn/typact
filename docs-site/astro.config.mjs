import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://typact.zzq.jl.cn',
  output: 'static',
  markdown: {
    shikiConfig: { theme: 'github-dark-default' },
  },
});
