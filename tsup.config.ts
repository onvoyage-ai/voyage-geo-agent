import { defineConfig } from 'tsup';

export default defineConfig({
  entry: ['src/index.ts', 'src/cli.ts'],
  format: ['esm'],
  dts: true,
  sourcemap: true,
  clean: true,
  target: 'node20',
  splitting: false,
  shims: false,
  banner: ({ format }) => {
    if (format === 'esm') {
      return {
        js: '#!/usr/bin/env node\n',
      };
    }
    return {};
  },
});
