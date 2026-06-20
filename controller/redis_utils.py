import json
import redis
import logging
import time
import threading
from typing import Dict, Any, Optional, Callable
from controller.config import REDIS_URL, REDIS_PIPELINE_QUEUE, REDIS_JOB_STATUS_PREFIX

logger = logging.getLogger(__name__)

class ControllerRedisManager:
    def __init__(self):
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        self.running = False
        self.worker_thread = None
        
    def set_job_status(self, job_id: str, status: str, message: str = "", result: Optional[Dict[str, Any]] = None):
        """
        Update job status in Redis.
        """
        job_status = {
            "status": status,
            "message": message,
            "updated_at": str(time.time())
        }
        
        if result:
            job_status["result"] = result
            
        try:
            key = f"{REDIS_JOB_STATUS_PREFIX}{job_id}"
            self.redis_client.setex(key, 86400, json.dumps(job_status))  # 24 hour TTL
            logger.info(f"Updated job {job_id} status to: {status}")
        except Exception as e:
            logger.error(f"Failed to set job status for {job_id}: {e}")
            raise
    
    def dequeue_pipeline_job(self) -> Optional[Dict[str, Any]]:
        """
        Dequeue a pipeline creation job from Redis.
        """
        try:
            job_data = self.redis_client.brpop(REDIS_PIPELINE_QUEUE, timeout=1)
            if job_data:
                return json.loads(job_data[1])
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue pipeline job: {e}")
            return None
    
    def start_worker(self, pipeline_processor: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Start the Redis worker thread to process pipeline creation jobs.
        """
        if self.running:
            logger.warning("Worker is already running")
            return
            
        self.running = True
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            args=(pipeline_processor,),
            daemon=True
        )
        self.worker_thread.start()
        logger.info("Redis worker started")
    
    def stop_worker(self):
        """
        Stop the Redis worker thread.
        """
        if not self.running:
            return
            
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Redis worker stopped")
    
    def _worker_loop(self, pipeline_processor: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Main worker loop that processes jobs from the queue.
        """
        logger.info("Worker loop started")
        
        while self.running:
            try:
                job = self.dequeue_pipeline_job()
                
                if job:
                    job_id = job.get("job_id")
                    logger.info(f"Processing job {job_id}")
                    
                    try:
                        # Update status to processing
                        self.set_job_status(job_id, "processing", "Pipeline creation in progress")
                        
                        # Process the job
                        result = pipeline_processor(job)
                        
                        # Update status to completed
                        self.set_job_status(
                            job_id, 
                            "completed", 
                            "Pipeline created successfully",
                            result
                        )
                        
                        logger.info(f"Job {job_id} completed successfully")
                        
                    except Exception as e:
                        error_msg = f"Job processing failed: {str(e)}"
                        logger.error(f"Job {job_id} failed: {error_msg}")
                        
                        # Update status to failed
                        self.set_job_status(
                            job_id, 
                            "failed", 
                            error_msg
                        )
                        
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(1)  # Brief pause before continuing
        
        logger.info("Worker loop stopped")

# Global Redis manager instance
redis_manager = ControllerRedisManager()
