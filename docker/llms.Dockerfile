FROM python:3.9-slim

WORKDIR /app

# Copy proto files and service implementation 
COPY proto/ /app/proto/
COPY llms/ /app/llms/

# Set working directory to the llms service directory
WORKDIR /app/llms

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default environment variables
ENV OLLAMA_HOST="http://ollama:11434"
ENV USE_OLLAMA_FALLBACK="true"
ENV LLM_KEY=""
ENV GRPC_PORT=50052

# Expose the gRPC port
EXPOSE 50052

# Run the LLM service
CMD python main.py

# ===========================================
# Configuration Options:
# ===========================================
# 
# Environment Variables:
#
# OLLAMA_HOST: URL of the Ollama API server (default: http://ollama:11434)
#   Example: -e OLLAMA_HOST="http://custom-ollama:11434"
#
# USE_OLLAMA_FALLBACK: Whether to use Ollama models as fallback (default: true)
#   Example: -e USE_OLLAMA_FALLBACK="false"
#
# LLM_KEY: API key for LLM provider
#   Example: -e LLM_KEY="your-api-key-here"
#
# GRPC_PORT: Port on which the gRPC service listens (default: 50052)
#   Example: -e GRPC_PORT=8080
#
# ===========================================
# Usage Examples:
# ===========================================
#
# Basic usage:
# docker run -p 50052:50052 artificialinsight/llms-service
#
# With custom configuration:
# docker run -p 8080:8080 \
#   -e GRPC_PORT=8080 \
#   -e OLLAMA_HOST="http://custom-ollama:11434" \
#   -e USE_OLLAMA_FALLBACK="true" \
#   -e LLM_KEY="sk-..." \
#   artificialinsight/llms-service
#
# ===========================================
# Notes:
# ===========================================
#
# - The service will automatically use Ollama models as fallback if the primary
#   LLM provider is unavailable or if its API key is not configured
#
# - To disable Ollama fallback functionality, set USE_OLLAMA_FALLBACK="false"
#
# - The service can work with only Ollama (without external API keys) if
#   you have Ollama running and accessible at the OLLAMA_HOST URL
