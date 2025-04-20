# ArtificialInsight - Scraping Service
# 
# This Dockerfile builds an image for the scraping microservice which
# provides web scraping functionality through a gRPC interface.

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create a non-root user to run the service
RUN groupadd -r scraper && \
    useradd -r -g scraper -d /app -s /sbin/nologin -c "Scraper service user" scraper && \
    chown -R scraper:scraper /app

# Environment variables for configuration
ENV SCRAPING_PORT=50051 \
    LOG_LEVEL=INFO \
    REQUEST_TIMEOUT=30 \
    MAX_WORKERS=10 \
    USER_AGENT="ArtificialInsightScraper/1.0"

# Copy requirements file and install dependencies
COPY scraping/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the necessary files for the service
# Proto files
COPY proto/ ./proto/
# Scraping service files
COPY scraping/ ./scraping/

# Generate gRPC code from proto files
RUN python -m grpc_tools.protoc -I./proto --python_out=./scraping/rpc --pyi_out=./scraping/rpc --grpc_python_out=./scraping/rpc ./proto/scraping.proto ./proto/common.proto

# Switch to the scraping directory
WORKDIR /app/scraping

# Switch to non-root user
USER scraper

# Expose the gRPC port
EXPOSE $SCRAPING_PORT

# Command to run the service
CMD ["python", "server.py"]

# === Configuration Instructions ===
#
# Environment Variables:
# - SCRAPING_PORT: Port on which the gRPC server will listen (default: 50051)
# - LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) (default: INFO)
# - REQUEST_TIMEOUT: Timeout in seconds for HTTP requests (default: 30)
# - MAX_WORKERS: Number of worker threads for the gRPC server (default: 10)
# - USER_AGENT: User agent string for HTTP requests (default: ArtificialInsightScraper/1.0)
#
# Example usage:
#
# Basic run:
# docker run -p 50051:50051 artificialinsight/scraping
#
# Custom configuration:
# docker run -p 8080:8080 -e SCRAPING_PORT=8080 -e LOG_LEVEL=DEBUG -e REQUEST_TIMEOUT=60 artificialinsight/scraping
#
# Integration with other services:
# In a Docker Compose setup, ensure the port is properly mapped and the service is accessible
# to other containers in the network.
#
# Sample docker-compose.yml entry:
#
# services:
#   scraping:
#     build:
#       context: ..
#       dockerfile: docker/scraping.Dockerfile
#     ports:
#       - "50051:50051"
#     environment:
#       - SCRAPING_PORT=50051
#       - LOG_LEVEL=INFO
#       - REQUEST_TIMEOUT=30
#       - MAX_WORKERS=10
