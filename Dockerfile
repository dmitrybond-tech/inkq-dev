# Frontend Dockerfile - Two-stage build
# Builder stage
FROM node:22-slim AS builder

WORKDIR /app

# Copy package files (package-lock.json is optional with * pattern)
COPY package.json package-lock.json* ./

# Install dependencies
# Use npm ci if package-lock.json is present (faster, reproducible); fallback to npm install for environments without a lockfile or if npm ci fails
RUN set +e; \
    if [ -f package-lock.json ]; then \
      npm ci; \
      if [ $? -ne 0 ]; then \
        echo "npm ci failed, falling back to npm install"; \
        npm install; \
      fi; \
    else \
      npm install; \
    fi; \
    set -e

# Build arguments (set before copying source for better caching)
ARG PUBLIC_API_BASE_URL=
ARG ASTRO_OUTPUT_MODE=static

# Set environment variables for Astro build
ENV PUBLIC_API_BASE_URL=${PUBLIC_API_BASE_URL}
ENV ASTRO_OUTPUT_MODE=${ASTRO_OUTPUT_MODE}

# Copy frontend source
COPY . .

# Remove prerender = false from pages to allow static build (build-time only, doesn't change source)
RUN find src/pages -name "*.astro" -type f -exec sed -i '/export const prerender = false/d' {} + 2>/dev/null || true

# Fix dynamic routes for static build
# 1. Replace getStaticPaths that return placeholder with empty array
# 2. Add getStaticPaths to dynamic routes that are missing it
RUN node -e "\
const fs = require('fs'); \
const path = require('path'); \
function findAstroFiles(dir) { \
  const files = []; \
  try { \
    const entries = fs.readdirSync(dir, { withFileTypes: true }); \
    for (const entry of entries) { \
      const fullPath = path.join(dir, entry.name); \
      if (entry.isDirectory()) { \
        files.push(...findAstroFiles(fullPath)); \
      } else if (entry.name.endsWith('.astro')) { \
        files.push(fullPath); \
      } \
    } \
  } catch (e) {} \
  return files; \
} \
findAstroFiles('src/pages').forEach(file => { \
  try { \
    let content = fs.readFileSync(file, 'utf8'); \
    const original = content; \
    const isDynamic = /\[.*\]/.test(path.basename(file)); \
    const hasGetStaticPaths = /export (async )?function getStaticPaths/.test(content); \
    \
    if (content.includes('placeholder') && hasGetStaticPaths) { \
      content = content.replace( \
        /export async function getStaticPaths\(\) \{[\s\S]*?return supportedLangs\.map\(\(lang\) => \(\{[\s\S]*?params: \{ lang, (?:slug|username|studioSlug): ['\"]placeholder['\"] \},[\s\S]*?\}\);[\s\S]*?\}/g, \
        'export async function getStaticPaths() {\\n  return [];\\n}' \
      ); \
    } \
    \
    if (isDynamic && !hasGetStaticPaths) { \
      const firstDash = content.indexOf('---'); \
      const secondDash = content.indexOf('---', firstDash + 3); \
      if (firstDash >= 0) { \
        let insertPos = firstDash + 3; \
        const afterFirstDash = content.indexOf('\\n', insertPos); \
        if (afterFirstDash > 0) insertPos = afterFirstDash + 1; \
        if (secondDash > 0 && insertPos < secondDash) { \
          const getStaticPathsCode = '\\nexport async function getStaticPaths() {\\n  return [];\\n}\\n'; \
          content = content.slice(0, insertPos) + getStaticPathsCode + content.slice(insertPos); \
        } \
      } \
    } \
    \
    if (content !== original) fs.writeFileSync(file, content, 'utf8'); \
  } catch (e) {} \
}); \
" || true

# Build the Astro app (verbose output for debugging)
RUN npm run build

# Runtime stage
FROM node:22-slim

WORKDIR /app

# Install serve globally
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /app/dist ./dist

# Expose port 4173
EXPOSE 4173

# Start serving static files
CMD ["serve", "-s", "dist", "-l", "4173"]

