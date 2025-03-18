import uvicorn
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get MongoDB connection details from .env
try:
    load_dotenv()
    
    # Log MongoDB connection details
    mongodb_url = os.getenv("MONGODB_URL", "Not configured")
    mongodb_db = os.getenv("MONGODB_DB", os.getenv("MONGODB_DB_NAME", "Not configured"))
    
    # Mask password in URL for logging
    masked_url = mongodb_url
    if "://" in mongodb_url:
        prefix, rest = mongodb_url.split("://", 1)
        if "@" in rest:
            auth, host = rest.split("@", 1)
            if ":" in auth:
                user, _ = auth.split(":", 1)
                masked_url = f"{prefix}://{user}:***@{host}"
    
    logger.info(f"MongoDB URL: {masked_url}")
    logger.info(f"MongoDB Database: {mongodb_db}")
except ImportError:
    logger.warning("python-dotenv not installed, using default environment variables")
except Exception as e:
    logger.error(f"Error loading environment variables: {str(e)}")

if __name__ == "__main__":
    # Get configuration from environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("DEBUG", "False").lower() == "true"
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    ) 
