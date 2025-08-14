# ACIM Guide Firebase Prometheus Exporter
# Multi-stage build for production deployment

FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

FROM node:18-alpine AS runtime

# Create non-root user for security
RUN addgroup -g 1001 -S acim && \
    adduser -S acim -u 1001

WORKDIR /app

# Copy dependencies from builder stage
COPY --from=builder /app/node_modules ./node_modules

# Copy application code
COPY prometheus-firebase-exporter.js ./
COPY package*.json ./

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data && \
    chown -R acim:acim /app

# Install curl for health checks
RUN apk add --no-cache curl

# Switch to non-root user
USER acim

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:9090/health || exit 1

# Expose metrics port
EXPOSE 9090

# Environment variables with defaults
ENV NODE_ENV=production
ENV METRICS_PORT=9090
ENV SCRAPE_INTERVAL=30000
ENV LOG_LEVEL=info

# Labels for container metadata
LABEL maintainer="ACIM Guide Team <devops@acim-guide.com>"
LABEL version="1.0.0"
LABEL description="Prometheus exporter for Firebase metrics with ACIM-specific monitoring"
LABEL org.opencontainers.image.source="https://github.com/acim-guide/monitoring"

# Start the application
CMD ["node", "prometheus-firebase-exporter.js"]
