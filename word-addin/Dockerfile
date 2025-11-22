# Word Add-in Server Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install all dependencies (including dev for build)
# Use npm install if package-lock.json doesn't exist, otherwise npm ci
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine AS runner

WORKDIR /app

# Install serve for static file serving
RUN npm install -g serve

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 addinuser && \
    mkdir -p /app/dist && \
    chown -R addinuser:nodejs /app

# Copy built files
COPY --from=builder --chown=addinuser:nodejs /app/dist ./dist
COPY --from=builder --chown=addinuser:nodejs /app/manifest.xml ./manifest.xml

USER addinuser

# Set default port (can be overridden by environment variable)
ENV PORT=3002

# Expose port
EXPOSE 3002

# Note: For production, HTTPS is required for Office Add-ins
# This serves the static files. In production, you'll need a reverse proxy with HTTPS
CMD sh -c "serve -s dist -l ${PORT}"
