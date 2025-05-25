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
            'service': 'controller'
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'grpc_method'):
            log_entry['grpc_method'] = record.grpc_method
            
        return json.dumps(log_entry)


def setup_logging(service_name: str = 'controller', log_level: str = 'INFO') -> logging.Logger:
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


# Custom log methods for common use cases
def log_grpc_request(logger: logging.Logger, method: str, request_id: str = None, user_id: str = None):
    """Log gRPC request with structured data"""
    extra = {'grpc_method': method}
    if request_id:
        extra['request_id'] = request_id
    if user_id:
        extra['user_id'] = user_id
    
    logger.info(f"Handling gRPC request: {method}", extra=extra)


def log_grpc_response(logger: logging.Logger, method: str, status: str, request_id: str = None, duration_ms: float = None):
    """Log gRPC response with structured data"""
    extra = {'grpc_method': method, 'status': status}
    if request_id:
        extra['request_id'] = request_id
    if duration_ms:
        extra['duration_ms'] = duration_ms
    
    logger.info(f"Completed gRPC request: {method} - {status}", extra=extra)


def log_service_call(logger: logging.Logger, service: str, method: str, request_id: str = None):
    """Log service-to-service calls"""
    extra = {'target_service': service, 'method': method}
    if request_id:
        extra['request_id'] = request_id
    
    logger.info(f"Calling {service} service: {method}", extra=extra)
