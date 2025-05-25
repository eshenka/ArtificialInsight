# ELK Stack for ArtificialInsight

## Overview

The ELK stack (Elasticsearch, Logstash, Kibana) with Filebeat provides comprehensive centralized logging for all ArtificialInsight microservices. This implementation captures, processes, stores, and visualizes logs from all system components.

## Current Status ✅

- **Elasticsearch**: Running on port 9200 with 140,295+ log documents
- **Logstash**: Processing logs on ports 5044 (Beats) and 5000 (UDP)  
- **Kibana**: Available at http://localhost:5601 with custom dashboards
- **Filebeat**: Collecting Docker container logs automatically

## Architecture

### Components
- **Elasticsearch**: Stores and indexes log data
- **Logstash**: Processes and transforms log data from various sources
- **Kibana**: Provides visualization and dashboards for log analysis
- **Filebeat**: Collects container logs and forwards to Logstash

### Log Flow
1. **Application Services** → Generate structured JSON logs
2. **Docker Logging Driver** → Captures container stdout/stderr
3. **Filebeat** → Collects Docker logs and forwards to Logstash (port 5044)
4. **UDP Direct Logging** → Services can send logs directly to Logstash (port 5000)
5. **Logstash** → Processes, filters, and structures logs
6. **Elasticsearch** → Stores and indexes logs with daily rotation
7. **Kibana** → Provides visualization and dashboard interface

### Index Pattern
- Daily indices: `microservices-logs-YYYY.MM.dd`
- Current index: `microservices-logs-2025.05.25`
- Retention: Configurable (default: no automatic deletion)

## Configuration Files

### Logstash
- `logstash/config/logstash.yml`: Main Logstash configuration
- `logstash/pipeline/logstash.conf`: Log processing pipeline configuration
  - **Inputs**: Beats (5044), UDP (5000) with JSON codec
  - **Filters**: JSON parsing, field extraction, service name cleanup
  - **Output**: Elasticsearch with daily index pattern

### Filebeat
- `filebeat/filebeat.yml`: Filebeat configuration
  - **Input**: Docker container logs from `/var/lib/docker/containers`
  - **Processors**: Docker metadata, JSON decoding, field renaming
  - **Output**: Logstash on port 5044

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

## Getting Started

### Starting the ELK Stack

The ELK stack is included in the main docker-compose.yaml. Start all services:

```bash
docker-compose up -d
```

Or start only the ELK stack:

```bash
docker-compose up -d elasticsearch logstash kibana filebeat
```

### Accessing the Services

- **Elasticsearch**: http://localhost:9200
- **Kibana**: http://localhost:5601

### Monitoring Logs

```bash
# Quick status check
python simple_monitor.py

# View recent logs in Kibana
# Open http://localhost:5601

# Search logs via API
curl "http://localhost:9200/microservices-logs-*/_search?q=service_name:controller"
```

## Log Structure

All logs are processed into a consistent structure:

```json
{
  "@timestamp": "2025-05-25T18:30:00.000Z",
  "service_name": "controller", 
  "log_level": "INFO",
  "log_message": "Server started successfully",
  "environment": "development",
  "project": "artificialinsight",
  "container": { "metadata": "..." }
}
```

### Original Service Log Format

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

## Services Currently Logging

- ✅ **controller** - Main orchestration service (gRPC method calls, service-to-service communication)
- ✅ **service-api** - REST API gateway (HTTP request/response logging, API endpoint usage)
- ✅ **llms** - AI/ML processing service (model usage, token consumption, response times)
- ✅ **scraping** - Web scraping service (URL requests, HTTP status codes, content analysis)
- ✅ **userdb** - User database service (database operations, authentication events)
- ✅ **vectordb** - Vector database service (vector operations, embeddings generation, search queries)
- ✅ **webui** - Frontend application (Nginx access logs, frontend errors, user interactions)
- ✅ **milvus-standalone** - Vector database engine
- ✅ **postgres** - PostgreSQL database
- ✅ **ELK stack components** - Infrastructure logging

## Application Logging Configuration

Each Python service uses structured logging via `logging_config.py`:

```python
import logging_config
logger = logging_config.get_logger(__name__)
logger.info("Service started", extra={"user_id": "123"})
```

### Sending Logs via UDP

```python
import socket
import json

log_data = {
    "timestamp": "2025-05-25T18:30:00Z",
    "service_name": "my-service", 
    "level": "INFO",
    "message": "Application started"
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(json.dumps(log_data).encode(), ('localhost', 5000))
sock.close()
```

## Kibana Dashboards

Pre-configured dashboards include:
- **ArtificialInsight Microservices Dashboard** - Overview of all services
- **Service Overview** - High-level metrics for all services
- **Log Volume Over Time** - Timeline visualization  
- **Logs by Service and Level** - Service health monitoring
- **Error Analysis** - Error patterns and troubleshooting
- **Performance Monitoring** - Response times and throughput
- **User Activity** - User interaction patterns

**Index Pattern**: `microservices-logs-*`

## Performance Metrics

- **Current Volume**: 140,295+ documents (53.2MB)
- **Ingestion Rate**: ~1,000+ logs/minute during active development
- **Storage**: Daily indices with automatic rotation
- **Query Performance**: Sub-second response times

## Log Retention

- Elasticsearch indices are created daily: `microservices-logs-YYYY.MM.DD`
- Docker container logs are rotated (max 10MB, 3 files per service)
- Configure retention policies in Elasticsearch for long-term storage

### Index Management

```bash
# View all indices
curl "localhost:9200/_cat/indices/microservices-logs-*?v"

# Delete old indices (example for cleanup)
curl -X DELETE "localhost:9200/microservices-logs-2025.05.24"
```

### Log Retention Policy
- Currently: Manual deletion required
- Recommended: Implement Elasticsearch ILM (Index Lifecycle Management)
- Suggested retention: 30 days for development, 90+ days for production

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

4. **Yellow cluster status**: Normal for single-node Elasticsearch
5. **High memory usage**: Adjust Elasticsearch heap size if needed
6. **Missing logs**: Check Docker logging driver configuration

### Debug Commands

```bash
# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

# View Elasticsearch indices
curl http://localhost:9200/_cat/indices

# Check Logstash logs
docker logs logstash

# Check Filebeat logs
docker logs filebeat

# Logstash health
curl "localhost:9600/_node/stats"

# Test log forwarding
python log_forwarder.py
```

## Performance Tuning

### Scaling Considerations

For production environments, consider:

1. **Elasticsearch**:
   - Increase heap size: `ES_JAVA_OPTS=-Xms1g -Xmx1g`
   - Add more nodes for horizontal scaling
   - Configure appropriate shard and replica settings
   - Can be clustered for high availability

2. **Logstash**:
   - Increase workers: `pipeline.workers: 4`
   - Tune batch size: `pipeline.batch.size: 250`
   - Add multiple Logstash instances for load balancing
   - Multiple instances for load distribution

3. **Filebeat**: Lightweight, minimal resource usage

4. **Resource Allocation**:
   - Monitor CPU and memory usage
   - Use SSD storage for better performance
   - Configure appropriate Docker resource limits
   - Monitor disk usage, implement retention policies

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

## Future Enhancements

1. **Alerting**: Implement Watcher for error detection
2. **Machine Learning**: Use Elastic ML for anomaly detection
3. **APM**: Add Elastic APM for application performance monitoring
4. **Security**: Implement authentication and SSL/TLS
5. **Backup**: Configure automated snapshots
6. **Monitoring**: Add Metricbeat for system metrics

## Files Modified/Created

- `docker/compose.yaml` - Added ELK stack services
- `logstash/config/logstash.yml` - Logstash configuration  
- `logstash/pipeline/logstash.conf` - Log processing pipeline
- `filebeat/filebeat.yml` - Filebeat configuration
- `kibana/dashboards/microservices-dashboard.json` - Kibana dashboard
- `elk_setup.py` - ELK setup automation script
- Various `logging_config.py` files - Structured logging setup

The ELK stack is now fully operational and providing comprehensive logging capabilities for the ArtificialInsight microservices architecture.
