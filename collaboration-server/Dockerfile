# Collaboration Server Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
# Use npm install if package-lock.json doesn't exist, otherwise npm ci
RUN if [ -f package-lock.json ]; then npm ci --production; else npm install --production; fi

# Copy source code
COPY . .

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 collabuser && \
    chown -R collabuser:nodejs /app

USER collabuser

# Expose port
EXPOSE 1234

ENV NODE_ENV=production
ENV COLLAB_PORT=1234

CMD ["node", "server.js"]
