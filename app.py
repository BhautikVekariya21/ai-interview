"""
Hugging Face Spaces entry point.
This file must be named 'app.py' in the root directory.
"""

import os
import sys
from pathlib import Path

# Ensure app directory is in path
sys.path.insert(0, str(Path(__file__).parent))

# Import the FastAPI app
from app.main import app

# Run with uvicorn when executed directly
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 7860))
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )