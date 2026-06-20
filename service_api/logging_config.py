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
            'service': 'service-api'
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields if present
        if hasattr(record, 'method'):
            log_entry['http_method'] = record.method
        if hasattr(record, 'path'):
            log_entry['http_path'] = record.path
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'response_time_ms'):
            log_entry['response_time_ms'] = record.response_time_ms
            
        return json.dumps(log_entry)


def setup_logging(service_name: str = 'service-api', log_level: str = 'INFO') -> logging.Logger:
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


def log_http_request(logger: logging.Logger, method: str, path: str, request_id: str = None, user_id: str = None):
    """Log HTTP request with structured data"""
    extra = {'method': method, 'path': path}
    if request_id:
        extra['request_id'] = request_id
    if user_id:
        extra['user_id'] = user_id
    
    logger.info(f"Handling HTTP request: {method} {path}", extra=extra)


def log_http_response(logger: logging.Logger, method: str, path: str, status_code: int, 
                     response_time_ms: float = None, request_id: str = None):
    """Log HTTP response with structured data"""
    extra = {'method': method, 'path': path, 'status_code': status_code}
    if response_time_ms:
        extra['response_time_ms'] = response_time_ms
    if request_id:
        extra['request_id'] = request_id
    
    logger.info(f"Completed HTTP request: {method} {path} - {status_code}", extra=extra)
