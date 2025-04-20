
import logging
from app import create_app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Creating Flask application...")
app = create_app()

if __name__ == "__main__":
    logger.debug("Configuring application...")
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    logger.info("Starting application on port 5000...")
    app.run(host='0.0.0.0', port=5000)
