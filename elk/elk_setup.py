#!/usr/bin/env python3
"""
Simple ELK Setup Script
"""

import requests
import time
import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
ELASTICSEARCH_URL = "http://elasticsearch:9200"
KIBANA_URL = "http://kibana:5601"
MAX_RETRIES = 30
RETRY_DELAY = 10

def wait_for_service(url, service_name):
    """Wait for a service to be available"""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                logger.info(f"{service_name} is ready")
                return True
        except requests.exceptions.RequestException:
            pass
        
        logger.info(f"Waiting for {service_name}... (attempt {attempt + 1}/{MAX_RETRIES})")
        time.sleep(RETRY_DELAY)
    
    return False

def create_kibana_index_pattern():
    """Create basic Kibana index pattern"""
    try:
        # Wait a bit more for Kibana to be fully ready
        time.sleep(10)
        
        index_pattern = {
            "attributes": {
                "title": "microservices-logs*",
                "timeFieldName": "@timestamp"
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "kbn-xsrf": "true"
        }
        
        response = requests.post(
            f"{KIBANA_URL}/api/saved_objects/index-pattern/microservices-logs",
            headers=headers,
            data=json.dumps(index_pattern),
            timeout=10
        )
        
        if response.status_code in [200, 409]:  # 409 = already exists
            logger.info("Kibana index pattern created/exists")
        else:
            logger.warning(f"Failed to create index pattern: {response.status_code}")
            
    except Exception as e:
        logger.warning(f"Error creating Kibana index pattern: {e}")

def send_test_log():
    """Send a test log entry"""
    try:
        test_log = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "level": "INFO",
            "service": "elk-setup",
            "message": "ELK stack setup completed successfully"
        }
        
        response = requests.post(
            f"{ELASTICSEARCH_URL}/microservices-logs/_doc",
            headers={"Content-Type": "application/json"},
            data=json.dumps(test_log),
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            logger.info("Test log sent to Elasticsearch")
        else:
            logger.warning(f"Failed to send test log: {response.status_code}")
            
    except Exception as e:
        logger.warning(f"Error sending test log: {e}")

def main():
    """Main setup process"""
    logger.info("Starting ELK stack setup...")
    
    # Wait for Elasticsearch
    if not wait_for_service(ELASTICSEARCH_URL, "Elasticsearch"):
        logger.error("Elasticsearch not available, exiting")
        sys.exit(1)
    
    # Wait for Kibana
    if not wait_for_service(KIBANA_URL, "Kibana"):
        logger.error("Kibana not available, exiting")
        sys.exit(1)
    
    # Create Kibana index pattern
    create_kibana_index_pattern()
    
    # Send test log
    send_test_log()
    
    logger.info("ELK setup completed")

if __name__ == "__main__":
    main()
