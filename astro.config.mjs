// @ts-check
import { defineConfig } from 'astro/config';
import node from '@astrojs/node';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
const isProd = process.env.NODE_ENV === 'production';
const port = Number(process.env.PORT) || (isProd ? 4173 : 4321);

export default defineConfig({
  output: 'server',
  adapter: node({ mode: 'standalone' }),
  server: {
    host: true,
    port,
  },
  vite: {
    plugins: [tailwindcss()]
  }
});