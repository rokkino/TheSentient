import asyncio
import sys
import os
import time
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from src.backend.services.scheduler_service import scheduler_service

async def mock_job():
    print(f"[TEST] Mock job executed at {datetime.now()}")
    scheduler_service.log_execution("mock_job", "SUCCESS", "Executed successfully")

async def test_scheduler():
    print("Testing Scheduler Service...")
    
    # Start scheduler
    scheduler_service.start()
    print(f"Scheduler running: {scheduler_service.scheduler.running}")
    
    # Add job
    scheduler_service.add_job(mock_job, 'interval', seconds=2, id='mock_job')
    print("Added mock job (every 2s)")
    
    # Wait for execution
    print("Waiting 5 seconds...")
    await asyncio.sleep(5)
    
    # Check logs
    logs = scheduler_service.get_logs()
    print(f"Logs found: {len(logs)}")
    for log in logs:
        print(f" - {log['timestamp']}: {log['job_name']} -> {log['status']}")
    
    # Shutdown
    scheduler_service.shutdown()
    print("Scheduler shutdown")

if __name__ == "__main__":
    asyncio.run(test_scheduler())
