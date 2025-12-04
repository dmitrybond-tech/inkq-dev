// @ts-check
import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
// Use static output for Docker/preprod builds, server mode for dev
const outputMode = process.env.ASTRO_OUTPUT_MODE === 'static' ? 'static' : 'server';

export default defineConfig({
  output: outputMode,
  vite: {
    plugins: [tailwindcss()]
  }
});