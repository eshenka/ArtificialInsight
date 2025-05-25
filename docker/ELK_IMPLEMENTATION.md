# ELK Stack Implementation for ArtificialInsight

## Overview
The ELK stack (Elasticsearch, Logstash, Kibana) with Filebeat has been successfully implemented and configured for comprehensive logging across all microservices in the ArtificialInsight project.

## Current Status ✅
- **Elasticsearch**: Running on port 9200 with 140,295+ log documents
- **Logstash**: Processing logs on ports 5044 (Beats) and 5000 (UDP)  
- **Kibana**: Available at http://localhost:5601 with custom dashboards
- **Filebeat**: Collecting Docker container logs automatically

## Architecture

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

### Logstash Pipeline (`docker/logstash/pipeline/logstash.conf`)
- **Inputs**: Beats (5044), UDP (5000) with JSON codec
- **Filters**: JSON parsing, field extraction, service name cleanup
- **Output**: Elasticsearch with daily index pattern

### Filebeat (`docker/filebeat/filebeat.yml`)
- **Input**: Docker container logs from `/var/lib/docker/containers`
- **Processors**: Docker metadata, JSON decoding, field renaming
- **Output**: Logstash on port 5044

### Docker Compose (`docker/compose.yaml`)
- All services configured with JSON logging driver
- ELK stack services with proper networking and volumes
- Health checks for service availability

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

## Services Currently Logging
- ✅ **controller** - Main orchestration service
- ✅ **service-api** - REST API gateway
- ✅ **llms** - AI/ML processing service  
- ✅ **scraping** - Web scraping service
- ✅ **userdb** - User database service (Rust)
- ✅ **vectordb** - Vector database service
- ✅ **webui** - Frontend application
- ✅ **milvus-standalone** - Vector database engine
- ✅ **postgres** - PostgreSQL database
- ✅ **ELK stack components** - Infrastructure logging

## Usage

### Starting the ELK Stack
```bash
cd docker
docker-compose up -d elasticsearch kibana logstash filebeat
```

### Monitoring Logs
```bash
# Quick status check
python simple_monitor.py

# View recent logs in Kibana
# Open http://localhost:5601

# Search logs via API
curl "http://localhost:9200/microservices-logs-*/_search?q=service_name:controller"
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

### Application Logging Configuration
Each Python service uses structured logging via `logging_config.py`:
```python
import logging_config
logger = logging_config.get_logger(__name__)
logger.info("Service started", extra={"user_id": "123"})
```

## Kibana Dashboards
- **ArtificialInsight Microservices Dashboard** - Overview of all services
- **Log Volume Over Time** - Timeline visualization  
- **Logs by Service and Level** - Service health monitoring
- **Index Pattern**: `microservices-logs-*`

## Performance Metrics
- **Current Volume**: 140,295+ documents (53.2MB)
- **Ingestion Rate**: ~1,000+ logs/minute during active development
- **Storage**: Daily indices with automatic rotation
- **Query Performance**: Sub-second response times

## Maintenance

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

### Scaling Considerations
- **Elasticsearch**: Can be clustered for high availability
- **Logstash**: Multiple instances for load distribution  
- **Filebeat**: Lightweight, minimal resource usage
- **Storage**: Monitor disk usage, implement retention policies

## Troubleshooting

### Common Issues
1. **Yellow cluster status**: Normal for single-node Elasticsearch
2. **High memory usage**: Adjust Elasticsearch heap size if needed
3. **Missing logs**: Check Docker logging driver configuration
4. **Logstash not processing**: Verify input port accessibility

### Log Files
- Elasticsearch: Check Docker logs `docker-compose logs elasticsearch`
- Logstash: Check Docker logs `docker-compose logs logstash`  
- Filebeat: Check Docker logs `docker-compose logs filebeat`

### Health Checks
```bash
# Elasticsearch health
curl "localhost:9200/_cluster/health"

# Logstash health
curl "localhost:9600/_node/stats"

# Test UDP logging
python log_forwarder.py
```

## Future Enhancements
1. **Alerting**: Implement Watcher for error detection
2. **Machine Learning**: Use Elastic ML for anomaly detection
3. **APM**: Add Elastic APM for application performance monitoring
4. **Security**: Implement authentication and SSL/TLS
5. **Backup**: Configure automated snapshots
6. **Monitoring**: Add Metricbeat for system metrics

## Files Modified/Created
- `docker/compose.yaml` - Added ELK stack services
- `docker/logstash/pipeline/logstash.conf` - Log processing pipeline
- `docker/logstash/config/logstash.yml` - Logstash configuration  
- `docker/filebeat/filebeat.yml` - Filebeat configuration
- `docker/kibana/dashboards/microservices-dashboard.json` - Kibana dashboard
- `docker/log_forwarder.py` - UDP logging test script
- `docker/simple_monitor.py` - ELK stack monitoring script
- Various `logging_config.py` files - Structured logging setup

The ELK stack is now fully operational and providing comprehensive logging capabilities for the ArtificialInsight microservices architecture.
