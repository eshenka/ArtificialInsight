import os
import grpc
import logging
import concurrent.futures
import signal
import time
from contextlib import contextmanager

from controller.rpc import controller_pb2_grpc
from controller.controller import ControllerServicer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('controller.server')


def load_config():
    """Load configuration from environment variables."""
    config = {
        'PORT': int(os.environ.get('CONTROLLER_PORT', '50050')),
        'HOST': os.environ.get('CONTROLLER_HOST', '[::]'),
        'USERDB_SERVICE': os.environ.get('USERDB_SERVICE', 'localhost:50051'),
        'VECTORDB_SERVICE': os.environ.get('VECTORDB_SERVICE', 'localhost:50052'),
        'SCRAPING_SERVICE': os.environ.get('SCRAPING_SERVICE', 'localhost:50053'),
        'LLM_SERVICE': os.environ.get('LLM_SERVICE', 'localhost:50054'),
        'MAX_WORKERS': int(os.environ.get('MAX_WORKERS', '10')),
    }
    
    logger.info(f"Loaded configuration: {config}")
    return config


@contextmanager
def graceful_exit(server):
    """Context manager for graceful server shutdown."""
    stop_event = concurrent.futures.Event()
    
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
    
    server = grpc.server(
        concurrent.futures.ThreadPoolExecutor(max_workers=config['MAX_WORKERS'])
    )
    
    controller_servicer = ControllerServicer(config)
    controller_pb2_grpc.add_ControllerServicer_to_server(controller_servicer, server)
    
    server_addr = f"{config['HOST']}:{config['PORT']}"
    server.add_insecure_port(server_addr)
    
    logger.info(f"Starting server on {server_addr}")
    server.start()
    
    with graceful_exit(server) as stop_event:
        logger.info("Server started successfully")
        
        while not stop_event.is_set():
            time.sleep(1)


if __name__ == '__main__':
    serve()
