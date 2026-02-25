import asyncio
import os
import sys

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.scheduler_jobs import update_bot_performance_job

async def main():
    print("Testing performance job execution...")
    await update_bot_performance_job()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
