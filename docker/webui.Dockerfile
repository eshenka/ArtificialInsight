# ArtificialInsight Web UI Dockerfile
# 
# This Dockerfile builds a container for the ArtificialInsight React web UI

# Build stage
FROM node:18 AS build

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY webui/package*.json ./
RUN npm ci

# Copy the rest of the application code
COPY webui/ ./

# Build the application
# Environment variables can be passed at build time if needed
# Example: --build-arg API_URL=http://api.example.com
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL:-/api}

# Fix for platform-specific dependencies
# Clean npm cache and node_modules to ensure we get the right binaries for the container platform
RUN rm -rf node_modules/.cache
RUN npm cache clean --force
RUN npm ci --prefer-offline

# Now build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy the built app to nginx serve directory
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Add configuration notes as comments
# ====================================
# CONFIGURATION OPTIONS:
# 
# Environment Variables:
# - VITE_API_BASE_URL: The URL of the backend API service (default: /api)
#   This must be set at build time using --build-arg
#
# Ports:
# - 80: The container exposes port 80 for the web UI
#
# Example build command:
# docker build -t artificialinsight-webui -f docker/webui.Dockerfile --build-arg VITE_API_BASE_URL=/api .
#
# Example run command:
# docker run -p 3000:80 artificialinsight-webui

# Expose port
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]