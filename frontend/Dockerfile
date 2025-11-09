# Stage 1: Build
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build application
RUN npm run build

# Stage 2: Runtime (for development)
FROM node:18-alpine

WORKDIR /app

# Copy package files and install dependencies (including dev dependencies for dev mode)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001 && \
    chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 5173

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:5173/ || exit 1

# Run application (default to dev mode, can be overridden in docker-compose)
CMD ["npm", "run", "dev"]
