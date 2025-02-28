from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import api_router
import logging
import uvicorn
import os

# Get absolute path to project root
PROJECT_ROOT = Path(__file__).parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
log_file_path = os.path.join(LOGS_DIR, "app.log")

print(f"Log directory: {LOGS_DIR}")  # Debug print
print(f"Log file path: {log_file_path}")  # Debug print

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, mode='a'),  # Append mode
        logging.StreamHandler()
    ],
    force=True
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cortex Document Service API",
    description="AI-powered document processing and analysis API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(api_router, prefix="/api", tags=["API"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Cortex API",
        "status": "operational"
    }

if __name__ == "__main__":
    logger.info("Starting the application...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)