// @ts-check
import { defineConfig } from 'astro/config';
import node from '@astrojs/node';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
// Use static output for Docker/preprod builds, server mode for dev
const outputMode = process.env.ASTRO_OUTPUT_MODE === 'static' ? 'static' : 'server';
const isProd = process.env.NODE_ENV === 'production';

export default defineConfig({
  output: outputMode,
  adapter: outputMode === 'server' ? node({ mode: 'standalone' }) : undefined,
  server: {
    host: true,
    port: isProd ? (Number(process.env.PORT) || 4173) : 4321,
  },
  vite: {
    plugins: [tailwindcss()]
  }
});