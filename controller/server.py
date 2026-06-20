import os
import grpc
import logging
import concurrent.futures
import signal
import time
import threading
from contextlib import contextmanager

from controller.rpc import controller_pb2_grpc
from controller.controller import ControllerServicer
from controller.logging_config import setup_logging
from controller.redis_utils import redis_manager

# Set up structured JSON logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger = setup_logging('controller', log_level)


def load_config():
    """Load configuration from environment variables."""
    config = {
        'PORT': int(os.environ.get('CONTROLLER_PORT', '50050')),
        'HOST': os.environ.get('CONTROLLER_HOST', '[::]'),
        'USERDB_SERVICE': os.environ.get('USERDB_SERVICE', 'localhost:50051'),
        'VECTORDB_SERVICE': os.environ.get('VECTORDB_SERVICE', 'localhost:50052'),
        'SCRAPING_SERVICE': os.environ.get('SCRAPING_SERVICE', 'localhost:50053'),
        'LLM_SERVICE': os.environ.get('LLM_SERVICE', 'localhost:50054'),
        'REDIS_URL': os.environ.get('REDIS_URL', 'redis://localhost:6379'),
        'MAX_WORKERS': int(os.environ.get('MAX_WORKERS', '10')),
        # Adding timeout configuration in seconds
        'DEFAULT_TIMEOUT': int(os.environ.get('DEFAULT_TIMEOUT', '30')),  
        'SCRAPING_TIMEOUT': int(os.environ.get('SCRAPING_TIMEOUT', '1800')),   # Scraping might take longer
        'LLM_TIMEOUT': int(os.environ.get('LLM_TIMEOUT', '60')),              # LLM generation can take time
        'USERDB_TIMEOUT': int(os.environ.get('USERDB_TIMEOUT', '15')),        # User DB is usually quick
        'VECTORDB_TIMEOUT': int(os.environ.get('VECTORDB_TIMEOUT', '300')),    # Vector search/insert can take time
    }
    
    logger.info(f"Loaded configuration: {config}")
    return config


@contextmanager
def graceful_exit(server):
    """Context manager for graceful server shutdown."""
    stop_event = threading.Event()
    
    def handle_signal(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        stop_event.set()
    
    original_handlers = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        original_handlers[sig] = signal.signal(sig, handle_signal)
    
    try:
        yield stop_event
    finally:
        logger.info("Stopping server...")
        server.stop(grace=5)
        
        # Restore original signal handlers
        for sig, handler in original_handlers.items():
            signal.signal(sig, handler)
        
        logger.info("Server stopped")


def serve():
    """Start the gRPC server."""
    config = load_config()
    
    # Add server-side keepalive options to handle client pings properly
    server_options = [
        # Allow pings even when there's no active streams
        ('grpc.keepalive_permit_without_calls', 1),
        # Minimum time between client pings (60 seconds)
        ('grpc.http2.min_time_between_pings_ms', 60000),
        # Allow up to 2 pings without sending data
        ('grpc.http2.max_pings_without_data', 2),
        # Ping timeout is 20 seconds
        ('grpc.keepalive_timeout_ms', 20000),
        # Maximum number of pings before considering client bad
        ('grpc.http2.max_ping_strikes', 3)
    ]
    
    server = grpc.server(
        concurrent.futures.ThreadPoolExecutor(max_workers=config['MAX_WORKERS']),
        options=server_options
    )
    
    controller_servicer = ControllerServicer(config)
    controller_pb2_grpc.add_ControllerServicer_to_server(controller_servicer, server)
    
    # Start Redis worker for pipeline creation
    redis_manager.start_worker(controller_servicer.process_pipeline_job)
    
    server_addr = f"{config['HOST']}:{config['PORT']}"
    server.add_insecure_port(server_addr)
    
    logger.info(f"Starting server on {server_addr}")
    server.start()
    
    with graceful_exit(server) as stop_event:
        logger.info("Server started successfully")
        
        try:
            while not stop_event.is_set():
                time.sleep(1)
        finally:
            # Stop Redis worker on shutdown
            redis_manager.stop_worker()


if __name__ == '__main__':
    serve()
