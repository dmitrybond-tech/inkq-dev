# Unified Diff - SSR Migration

## package.json

```diff
 {
   "name": "inkq-v1-0",
   "type": "module",
   "version": "0.0.1",
   "scripts": {
     "dev": "astro dev",
     "build": "astro build",
     "preview": "astro preview",
+    "start": "NODE_ENV=production node dist/server/entry.mjs",
     "astro": "astro"
   },
   "dependencies": {
+    "@astrojs/node": "^9.5.1",
     "@tailwindcss/vite": "^4.1.17",
     "astro": "^5.16.0",
     "tailwindcss": "^4.1.17"
   }
 }
```

## astro.config.mjs

```diff
 // @ts-check
 import { defineConfig } from 'astro/config';
+import node from '@astrojs/node';
 import tailwindcss from '@tailwindcss/vite';
 
 // https://astro.build/config
 // Use static output for Docker/preprod builds, server mode for dev
 const outputMode = process.env.ASTRO_OUTPUT_MODE === 'static' ? 'static' : 'server';
+const isProd = process.env.NODE_ENV === 'production';
 
 export default defineConfig({
   output: outputMode,
+  adapter: outputMode === 'server' ? node({ mode: 'standalone' }) : undefined,
+  server: {
+    host: true,
+    port: isProd ? (Number(process.env.PORT) || 4173) : 4321,
+  },
   vite: {
     plugins: [tailwindcss()]
   }
 });
```

## Dockerfile

```diff
 # Build arguments (set before copying source for better caching)
 ARG PUBLIC_API_BASE_URL=
-ARG ASTRO_OUTPUT_MODE=static
+ARG ASTRO_OUTPUT_MODE=server
 
 # Set environment variables for Astro build
 ENV PUBLIC_API_BASE_URL=${PUBLIC_API_BASE_URL}
 ENV ASTRO_OUTPUT_MODE=${ASTRO_OUTPUT_MODE}
+ENV NODE_ENV=production
 
 # Copy frontend source
 COPY . .
 
-# Remove prerender = false from pages to allow static build (build-time only, doesn't change source)
-RUN find src/pages -name "*.astro" -type f -exec sed -i '/export const prerender = false/d' {} + 2>/dev/null || true
-
-# Fix dynamic routes for static build
-# 1. Replace getStaticPaths that return placeholder with empty array
-# 2. Add getStaticPaths to dynamic routes that are missing it
-RUN node -e "\
-const fs = require('fs'); \
-const path = require('path'); \
-function findAstroFiles(dir) { \
-  const files = []; \
-  try { \
-    const entries = fs.readdirSync(dir, { withFileTypes: true }); \
-    for (const entry of entries) { \
-      const fullPath = path.join(dir, entry.name); \
-      if (entry.isDirectory()) { \
-        files.push(...findAstroFiles(fullPath)); \
-      } else if (entry.name.endsWith('.astro')) { \
-        files.push(fullPath); \
-      } \
-    } \
-  } catch (e) {} \
-  return files; \
-} \
-findAstroFiles('src/pages').forEach(file => { \
-  try { \
-    let content = fs.readFileSync(file, 'utf8'); \
-    const original = content; \
-    const isDynamic = /\[.*\]/.test(path.basename(file)); \
-    const hasGetStaticPaths = /export (async )?function getStaticPaths/.test(content); \
-    \
-    if (content.includes('placeholder') && hasGetStaticPaths) { \
-      content = content.replace( \
-        /export async function getStaticPaths\(\) \{[\s\S]*?return supportedLangs\.map\(\(lang\) => \(\{[\s\S]*?params: \{ lang, (?:slug|username|studioSlug): ['\"]placeholder['\"] \},[\s\S]*?\}\);[\s\S]*?\}/g, \
-        'export async function getStaticPaths() {\\n  return [];\\n}' \
-      ); \
-    } \
-    \
-    if (isDynamic && !hasGetStaticPaths) { \
-      const firstDash = content.indexOf('---'); \
-      const secondDash = content.indexOf('---', firstDash + 3); \
-      if (firstDash >= 0) { \
-        let insertPos = firstDash + 3; \
-        const afterFirstDash = content.indexOf('\\n', insertPos); \
-        if (afterFirstDash > 0) insertPos = afterFirstDash + 1; \
-        if (secondDash > 0 && insertPos < secondDash) { \
-          const getStaticPathsCode = '\\nexport async function getStaticPaths() {\\n  return [];\\n}\\n'; \
-          content = content.slice(0, insertPos) + getStaticPathsCode + content.slice(insertPos); \
-        } \
-      } \
-    } \
-    \
-    if (content !== original) fs.writeFileSync(file, content, 'utf8'); \
-  } catch (e) {} \
-}); \
-" || true
-
-# Build the Astro app (verbose output for debugging)
+# Build the Astro app (SSR mode)
 RUN npm run build
 
 # Runtime stage
 FROM node:22-slim
 
 WORKDIR /app
 
-# Install serve globally
-RUN npm install -g serve
-
 # Copy built files from builder (includes dist/server/entry.mjs for SSR)
 COPY --from=builder /app/dist ./dist
+COPY --from=builder /app/package.json ./package.json
 
 # Set production environment
+ENV NODE_ENV=production
 ENV PORT=4173
 
 # Expose port 4173
 EXPOSE 4173
 
-# Start serving static files
-CMD ["serve", "-s", "dist", "-l", "4173"]
+# Start Node SSR server
+CMD ["node", "dist/server/entry.mjs"]
```

