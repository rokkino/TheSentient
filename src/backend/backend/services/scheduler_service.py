import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from datetime import datetime
import threading

# Configure logging
logging.basicConfig()
logger = logging.getLogger("scheduler")
logger.setLevel(logging.INFO)

class SchedulerService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SchedulerService, cls).__new__(cls)
                cls._instance.scheduler = AsyncIOScheduler()
                cls._instance.jobs_log = []  # In-memory log for now
                
                # Setup memory path
                import os
                current_dir = os.path.dirname(os.path.abspath(__file__))
                backend_dir = os.path.dirname(current_dir)
                cls._instance.log_dir = os.path.join(backend_dir, 'memory', 'bot', 'logs')
                os.makedirs(cls._instance.log_dir, exist_ok=True)
                
            return cls._instance

    def start(self):
        """Start the scheduler if not already running."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down")

    def add_job(self, func, trigger, **kwargs):
        """Add a job to the scheduler."""
        try:
            job = self.scheduler.add_job(func, trigger, **kwargs)
            logger.info(f"Job added: {job.id}")
            return job.id
        except Exception as e:
            logger.error(f"Error adding job: {e}")
            return None

    def remove_job(self, job_id):
        """Remove a job from the scheduler."""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job removed: {job_id}")
            return True
        except JobLookupError:
            logger.warning(f"Job not found: {job_id}")
            return False
        except Exception as e:
            logger.error(f"Error removing job: {e}")
            return False

    def get_jobs(self):
        """Get list of scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs

    def log_execution(self, job_name, status, message=""):
        """Log job execution (can be expanded to DB)."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "job_name": job_name,
            "status": status,
            "message": message
        }
        self.jobs_log.append(entry)
        # Keep only last 100 logs
        if len(self.jobs_log) > 100:
            self.jobs_log.pop(0)
            
        # Save to file
        try:
            import json
            import os
            
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = f"scheduler_log_{date_str}.json"
            file_path = os.path.join(self.log_dir, filename)
            
            # Append to list in file
            data = []
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except:
                    data = []
            
            data.append(entry)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving scheduler log: {e}")

    def get_logs(self):
        """Get execution logs."""
        return sorted(self.jobs_log, key=lambda x: x["timestamp"], reverse=True)

# Global instance
scheduler_service = SchedulerService()
