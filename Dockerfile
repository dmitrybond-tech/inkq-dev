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
ARG ASTRO_OUTPUT_MODE=server

# Set environment variables for Astro build
ENV PUBLIC_API_BASE_URL=${PUBLIC_API_BASE_URL}
ENV ASTRO_OUTPUT_MODE=${ASTRO_OUTPUT_MODE}
ENV NODE_ENV=production

# Copy frontend source
COPY . .

# Build the Astro app (SSR mode)
RUN npm run build

# Runtime stage
FROM node:22-slim

WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV PORT=4173

# Copy built files from builder (includes dist/server/entry.mjs for SSR)
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./package.json

# Expose port 4173
EXPOSE 4173

# Start Node SSR server
CMD ["node", "dist/server/entry.mjs"]

