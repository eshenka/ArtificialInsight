# ELK Stack Logging Setup for ArtificialInsight

This directory contains the configuration for the ELK (Elasticsearch, Logstash, Kibana) stack that provides centralized logging for all ArtificialInsight microservices.

## Overview

The ELK stack consists of:
- **Elasticsearch**: Stores and indexes log data
- **Logstash**: Processes and transforms log data from various sources
- **Kibana**: Provides visualization and dashboards for log analysis

## Architecture

```
Microservices → Docker JSON Logs → Logstash → Elasticsearch → Kibana
```

All microservices are configured with structured JSON logging that includes:
- Timestamp (ISO 8601 format)
- Service name
- Log level
- Message
- Additional contextual fields (request IDs, user IDs, etc.)

## Configuration Files

### Logstash
- `logstash/config/logstash.yml`: Main Logstash configuration
- `logstash/pipeline/logstash.conf`: Log processing pipeline configuration

### Kibana
- `kibana/dashboards/`: Pre-configured dashboards for log visualization

## Services and Ports

| Service | Port | Description |
|---------|------|-------------|
| Elasticsearch | 9200 | REST API and data storage |
| Logstash | 5044 | Beats input |
| Logstash | 5000 | UDP input for custom logs |
| Kibana | 5601 | Web interface |

## Environment Variables

Configure these variables in your `.env` file:

```bash
# ELK Stack Configuration
ELASTICSEARCH_PORT=9200
LOGSTASH_PORT=5044
LOGSTASH_UDP_PORT=5000
KIBANA_PORT=5601
LOG_LEVEL=INFO
```

## Starting the ELK Stack

The ELK stack is included in the main docker-compose.yaml. Start all services:

```bash
docker-compose up -d
```

Or start only the ELK stack:

```bash
docker-compose up -d elasticsearch logstash kibana
```

## Accessing the Services

- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601

## Log Structure

All microservices produce structured JSON logs with the following format:

```json
{
  "timestamp": "2025-01-20T10:30:00.000Z",
  "level": "INFO",
  "name": "controller.server",
  "message": "Handling gRPC request: CreatePipeline",
  "service": "controller",
  "grpc_method": "CreatePipeline",
  "request_id": "req_123456",
  "user_id": "user_789"
}
```

## Service-Specific Logging

### Controller Service
- gRPC method calls
- Service-to-service communication
- Request/response tracking

### LLM Service
- Model usage and performance
- Token consumption
- Response times

### Scraping Service
- URL scraping requests
- HTTP status codes
- Content analysis

### Service API
- HTTP request/response logging
- API endpoint usage
- Error tracking

### User Database (Rust)
- Database operations
- Authentication events
- User management actions

### Vector Database
- Vector operations
- Embeddings generation
- Search queries

### Web UI
- Nginx access logs
- Frontend errors
- User interactions

## Kibana Dashboards

Pre-configured dashboards include:
- **Service Overview**: High-level metrics for all services
- **Error Analysis**: Error patterns and troubleshooting
- **Performance Monitoring**: Response times and throughput
- **User Activity**: User interaction patterns

## Log Retention

- Elasticsearch indices are created daily: `microservices-YYYY.MM.DD`
- Docker container logs are rotated (max 10MB, 3 files per service)
- Configure retention policies in Elasticsearch for long-term storage

## Troubleshooting

### Common Issues

1. **Elasticsearch won't start**
   - Check available disk space
   - Verify memory limits (minimum 512MB)
   - Check port conflicts

2. **Logstash not receiving logs**
   - Verify network connectivity between services
   - Check Logstash pipeline configuration
   - Ensure services are using correct log format

3. **Kibana shows no data**
   - Check if Elasticsearch contains indices
   - Verify index patterns in Kibana
   - Ensure time range is correct

### Debug Commands

```bash
# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# View Elasticsearch indices
curl http://localhost:9200/_cat/indices

# Check Logstash logs
docker logs logstash

# Test log forwarding
python docker/log_forwarder.py
```

## Performance Tuning

For production environments, consider:

1. **Elasticsearch**:
   - Increase heap size: `ES_JAVA_OPTS=-Xms1g -Xmx1g`
   - Add more nodes for horizontal scaling
   - Configure appropriate shard and replica settings

2. **Logstash**:
   - Increase workers: `pipeline.workers: 4`
   - Tune batch size: `pipeline.batch.size: 250`
   - Add multiple Logstash instances for load balancing

3. **Resource Allocation**:
   - Monitor CPU and memory usage
   - Use SSD storage for better performance
   - Configure appropriate Docker resource limits

## Security Considerations

For production deployments:

1. Enable Elasticsearch security features
2. Configure SSL/TLS for all connections
3. Implement proper authentication and authorization
4. Use secure communication between services
5. Regular security updates for all components

## Monitoring

Monitor the ELK stack itself:
- Elasticsearch cluster health
- Logstash pipeline performance
- Kibana response times
- Disk usage and log retention
- Index optimization and cleanup
