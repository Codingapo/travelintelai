import os
import sys

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
