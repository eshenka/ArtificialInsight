import json
import uuid
import redis
from typing import Dict, Any, Optional
from config import REDIS_URL, REDIS_PIPELINE_QUEUE, REDIS_JOB_STATUS_PREFIX
import logging

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self):
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        
    def enqueue_pipeline_job(self, job_data: Dict[str, Any]) -> str:
        """
        Enqueue a pipeline creation job and return job ID.
        """
        job_id = str(uuid.uuid4())
        
        # Add job metadata
        job_payload = {
            "job_id": job_id,
            "status": "queued",
            "created_at": str(uuid.uuid1().time),
            **job_data
        }
        
        try:
            # Set initial job status
            self.set_job_status(job_id, "queued", "Pipeline creation job queued")
            
            # Push job to queue
            self.redis_client.lpush(REDIS_PIPELINE_QUEUE, json.dumps(job_payload))
            
            logger.info(f"Enqueued pipeline job {job_id} for user {job_data.get('user_name', 'unknown')}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to enqueue pipeline job: {e}")
            raise
    
    def set_job_status(self, job_id: str, status: str, message: str = "", result: Optional[Dict[str, Any]] = None):
        """
        Update job status in Redis.
        """
        job_status = {
            "status": status,
            "message": message,
            "updated_at": str(uuid.uuid1().time)
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
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status from Redis.
        """
        try:
            key = f"{REDIS_JOB_STATUS_PREFIX}{job_id}"
            status_data = self.redis_client.get(key)
            
            if status_data:
                return json.loads(status_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return None
    
    def dequeue_pipeline_job(self) -> Optional[Dict[str, Any]]:
        """
        Dequeue a pipeline creation job from Redis.
        Used by the controller worker.
        """
        try:
            job_data = self.redis_client.brpop(REDIS_PIPELINE_QUEUE, timeout=1)
            if job_data:
                return json.loads(job_data[1])
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue pipeline job: {e}")
            return None

# Global Redis manager instance
redis_manager = RedisManager()
