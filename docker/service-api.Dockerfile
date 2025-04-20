# Use Python 3.11 slim as the base image for a smaller footprint
FROM python:3.11-slim

# Set working directory in the container
WORKDIR /app

# Set environment variables
# These can be overridden at runtime with docker run -e or in docker-compose.yml
ENV CONTROLLER_ADDR="localhost:50051" \
    GATEWAY_HTTP_PORT=8000

# Copy requirements file and install dependencies
COPY ./service_api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./service_api /app/
COPY ./proto /app/proto

# Generate Python code from protobuf definitions
RUN mkdir -p /app/rpc && \
    python -m grpc_tools.protoc \
    --proto_path=/app/proto \
    --python_out=/app/rpc \
    --grpc_python_out=/app/rpc \
    /app/proto/controller.proto \
    /app/proto/common.proto

# Create a non-root user to run the application
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Expose the HTTP port
EXPOSE ${GATEWAY_HTTP_PORT}

# Command to run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "${GATEWAY_HTTP_PORT}"]

# ===================================================================================
# Configuration Instructions
# ===================================================================================
#
# This Docker container can be configured using the following environment variables:
#
# 1. CONTROLLER_ADDR (default: localhost:50051)
#    - The address of the Controller gRPC service in the format "host:port"
#    - Example: CONTROLLER_ADDR=controller-service:50051
#
# 2. GATEWAY_HTTP_PORT (default: 8000)
#    - The port number on which the gateway service will listen for HTTP requests
#    - Example: GATEWAY_HTTP_PORT=8080
#
# Example usage with Docker:
#   docker run -d \
#     -e CONTROLLER_ADDR=controller-service:50051 \
#     -e GATEWAY_HTTP_PORT=8080 \
#     -p 8080:8080 \
#     --name service-api-gateway \
#     artificial-insight/service-api
#
# Example usage with Docker Compose:
#   services:
#     service-api:
#       image: artificial-insight/service-api
#       environment:
#         - CONTROLLER_ADDR=controller-service:50051
#         - GATEWAY_HTTP_PORT=8080
#       ports:
#         - "8080:8080"
#       depends_on:
#         - controller-service
#
# Health check:
#   The service exposes FastAPI's auto-generated documentation at /docs 
#   which can be used for health checking.
# ===================================================================================
