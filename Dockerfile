# Frontend Dockerfile - Two-stage build
# Builder stage
FROM node:22-slim AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

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

