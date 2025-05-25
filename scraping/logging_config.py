import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging compatible with ELK stack
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
            'service': 'scraping'
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields if present
        if hasattr(record, 'url'):
            log_entry['url'] = record.url
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'response_time_ms'):
            log_entry['response_time_ms'] = record.response_time_ms
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'content_length'):
            log_entry['content_length'] = record.content_length
            
        return json.dumps(log_entry)


def setup_logging(service_name: str = 'scraping', log_level: str = 'INFO') -> logging.Logger:
    """
    Setup structured JSON logging for the service
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Return service-specific logger
    return logging.getLogger(service_name)


def log_scraping_request(logger: logging.Logger, url: str, request_id: str = None):
    """Log scraping request with structured data"""
    extra = {'url': url}
    if request_id:
        extra['request_id'] = request_id
    
    logger.info(f"Starting scraping request for: {url}", extra=extra)


def log_scraping_response(logger: logging.Logger, url: str, status_code: int = None, 
                         content_length: int = None, response_time_ms: float = None, request_id: str = None):
    """Log scraping response with structured data"""
    extra = {'url': url}
    if status_code:
        extra['status_code'] = status_code
    if content_length:
        extra['content_length'] = content_length
    if response_time_ms:
        extra['response_time_ms'] = response_time_ms
    if request_id:
        extra['request_id'] = request_id
    
    logger.info(f"Completed scraping request for: {url}", extra=extra)
