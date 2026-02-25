import asyncio
import sys
import os

# Emulate backend path
BACKEND_DIR = os.path.join(os.getcwd(), "src", "backend", "backend")
sys.path.insert(0, BACKEND_DIR)

from services.scheduler_jobs import execute_orders_job

if __name__ == "__main__":
    asyncio.run(execute_orders_job())
