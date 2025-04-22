import os
import logging

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Import app after logging configuration
from app import app

# Only run the development server when this file is run directly
if __name__ == "__main__":
    try:
        port = int(os.environ.get('PORT', 5000))
        debug = bool(os.environ.get('FLASK_DEBUG', True))
        logger.info(f"Starting development server on port {port} with debug={debug}...")
        app.run(host='0.0.0.0', port=port, debug=debug)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
    raise
