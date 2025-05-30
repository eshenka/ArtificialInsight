# ArtificialInsight Web UI Dockerfile
# 
# This Dockerfile builds a container for the ArtificialInsight React web UI

# Build stage
FROM node:18 AS build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json first for better caching
COPY webui-new/package*.json ./

# Install dependencies
RUN npm install react-router-dom
RUN npm install

# Copy the application code
COPY webui-new/ ./

# Show files for debugging
RUN ls -la

# Build the application
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL:-/api}

# Clean npm cache and build
RUN npm cache clean --force
RUN npm run build

# Show what was built
RUN ls -la dist/

# Production stage
FROM nginx:alpine

# Remove default nginx static resources
RUN rm -rf /usr/share/nginx/html/*

# Copy the built app to nginx serve directory
COPY --from=build /app/dist/ /usr/share/nginx/html/

# For direct HTML file serving
COPY webui-new/playground.html /usr/share/nginx/html/playground/index.html
COPY webui-new/create-pipeline.html /usr/share/nginx/html/create-pipeline/index.html

# Copy custom nginx configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Show what's in the nginx html directory
RUN ls -la /usr/share/nginx/html/

# Expose port
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]
