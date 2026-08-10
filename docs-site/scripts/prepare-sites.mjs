import { cp, mkdir, writeFile } from 'node:fs/promises';

await mkdir('dist/server', { recursive: true });
await mkdir('dist/.openai', { recursive: true });

await writeFile(
  'dist/server/index.js',
  `export default {
  async fetch(request, env) {
    if (env.ASSETS?.fetch) return env.ASSETS.fetch(request);
    return new Response('Static assets binding is unavailable.', { status: 503 });
  },
};\n`,
);

await cp('.openai/hosting.json', 'dist/.openai/hosting.json');
