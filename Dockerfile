# === Builder stage ===
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci || npm install

# Build arguments (set before copying source for better caching)
ARG PUBLIC_API_BASE_URL=

# Set environment variables for Astro build
ENV PUBLIC_API_BASE_URL=${PUBLIC_API_BASE_URL}
ENV NODE_ENV=production
ENV PORT=4173

# Copy the rest of the frontend source
COPY . .

# Build Astro in server (SSR) mode
RUN npm run build

# === Runtime stage ===
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=4173

# Copy built SSR assets
COPY --from=builder /app/dist ./dist

# Copy package files so we can install only runtime deps if needed
COPY package.json package-lock.json* ./

# Install production dependencies only (omit devDeps)
RUN npm ci --omit=dev || npm install --omit=dev

# Expose the port Astro will listen on
EXPOSE 4173

# Start the Astro SSR server
CMD ["node", "dist/server/entry.mjs"]

