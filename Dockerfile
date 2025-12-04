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

# Copy frontend source
COPY . .

# Build arguments
ARG PUBLIC_API_BASE_URL=
ARG ASTRO_OUTPUT_MODE=static

# Set environment variables for Astro build
ENV PUBLIC_API_BASE_URL=${PUBLIC_API_BASE_URL}
ENV ASTRO_OUTPUT_MODE=${ASTRO_OUTPUT_MODE}

# Build the Astro app
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

