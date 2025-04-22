# Build stage
FROM rust:1.86-slim as builder

WORKDIR /usr/src/app

# Install required dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    pkg-config \
    libssl-dev \
    protobuf-compiler && \
    rm -rf /var/lib/apt/lists/*

# Copy the Cargo.toml and Cargo.lock files first to leverage Docker cache
COPY userdb/Cargo.toml userdb/Cargo.lock* ./userdb/
COPY proto ./proto/

# Create a dummy main.rs to build dependencies
RUN mkdir -p userdb/src && \
    echo "fn main() {}" > userdb/src/main.rs && \
    echo "pub fn dummy() {}" > userdb/src/lib.rs && \
    cd userdb && \
    cargo build --release && \
    rm -f src/*.rs

# Copy the actual source code
COPY userdb/src ./userdb/src
COPY userdb/build.rs ./userdb/
COPY userdb/migrations ./userdb/migrations/

# Build the application
RUN cd userdb && cargo build --release

# Runtime stage
FROM debian:bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    libssl3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the binary from the builder stage
COPY --from=builder /usr/src/app/userdb/target/release/userdb .

# Environment variables
# USERDB_PG_URL - PostgreSQL connection URL (required)
# USERDB_ADDR - Address to bind the service (default: localhost)
# USERDB_PORT - Port to bind the service (default: 2780)

# Set default environment variables
ENV USERDB_ADDR=0.0.0.0
ENV USERDB_PORT=2780
ENV RUST_LOG=info

# Expose the port
EXPOSE 2780

# Command to run
ENTRYPOINT ["./userdb"]

# ==============================================
# Configuration Notes:
# ==============================================
#
# Required Environment Variables:
# - USERDB_PG_URL: PostgreSQL connection string
#   Format: postgres://username:password@hostname:port/database
#   Example: postgres://postgres:password@postgres:5432/aiusers
#
# Optional Environment Variables:
# - USERDB_ADDR: Address to bind the service (default: 0.0.0.0 in container)
# - USERDB_PORT: Port to bind the service (default: 2780)
# - RUST_LOG: Log level (trace, debug, info, warn, error) (default: info)
#
# Example docker run command:
# docker run -d --name userdb \
#   -e USERDB_PG_URL=postgres://postgres:password@postgres:5432/aiusers \
#   -e RUST_LOG=info \
#   -p 2780:2780 \
#   userdb-service
#
# For docker-compose:
# userdb:
#   build:
#     context: .
#     dockerfile: docker/userdb.Dockerfile
#   environment:
#     - USERDB_PG_URL=postgres://postgres:password@postgres:5432/aiusers
#     - RUST_LOG=info
#   ports:
#     - "2780:2780"
#   depends_on:
#     - postgres
#
# The service automatically:
# - Creates the database if it doesn't exist
# - Runs all migrations from ./migrations directory
# - Exposes the gRPC service on the configured port
