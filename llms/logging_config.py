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
            'service': 'llms'
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields if present
        if hasattr(record, 'model_name'):
            log_entry['model_name'] = record.model_name
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'tokens_used'):
            log_entry['tokens_used'] = record.tokens_used
        if hasattr(record, 'response_time_ms'):
            log_entry['response_time_ms'] = record.response_time_ms
            
        return json.dumps(log_entry)


def setup_logging(service_name: str = 'llms', log_level: str = 'INFO') -> logging.Logger:
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


def log_llm_request(logger: logging.Logger, model: str, prompt_length: int, request_id: str = None):
    """Log LLM request with structured data"""
    extra = {'model_name': model, 'prompt_length': prompt_length}
    if request_id:
        extra['request_id'] = request_id
    
    logger.info(f"Processing LLM request with model: {model}", extra=extra)


def log_llm_response(logger: logging.Logger, model: str, tokens_used: int = None, response_time_ms: float = None, request_id: str = None):
    """Log LLM response with structured data"""
    extra = {'model_name': model}
    if tokens_used:
        extra['tokens_used'] = tokens_used
    if response_time_ms:
        extra['response_time_ms'] = response_time_ms
    if request_id:
        extra['request_id'] = request_id
    
    logger.info(f"Completed LLM request with model: {model}", extra=extra)
