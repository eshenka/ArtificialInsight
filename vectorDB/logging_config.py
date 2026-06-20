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
            'service': 'vectordb'
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields if present
        if hasattr(record, 'collection_name'):
            log_entry['collection_name'] = record.collection_name
        if hasattr(record, 'vector_dimension'):
            log_entry['vector_dimension'] = record.vector_dimension
        if hasattr(record, 'document_count'):
            log_entry['document_count'] = record.document_count
        if hasattr(record, 'search_results'):
            log_entry['search_results'] = record.search_results
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'operation_time_ms'):
            log_entry['operation_time_ms'] = record.operation_time_ms
            
        return json.dumps(log_entry)


def setup_logging(service_name: str = 'vectordb', log_level: str = 'INFO') -> logging.Logger:
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


def log_vector_operation(logger: logging.Logger, operation: str, collection: str = None, 
                        count: int = None, request_id: str = None):
    """Log vector database operations with structured data"""
    extra = {'operation': operation}
    if collection:
        extra['collection_name'] = collection
    if count:
        extra['document_count'] = count
    if request_id:
        extra['request_id'] = request_id
    
    logger.info(f"Vector operation: {operation}", extra=extra)


def log_search_operation(logger: logging.Logger, collection: str, query_vector_dim: int = None,
                        results_count: int = None, search_time_ms: float = None, request_id: str = None):
    """Log vector search operations with structured data"""
    extra = {'collection_name': collection, 'operation': 'search'}
    if query_vector_dim:
        extra['vector_dimension'] = query_vector_dim
    if results_count:
        extra['search_results'] = results_count
    if search_time_ms:
        extra['operation_time_ms'] = search_time_ms
    if request_id:
        extra['request_id'] = request_id
    
    logger.info(f"Vector search in collection: {collection}", extra=extra)
