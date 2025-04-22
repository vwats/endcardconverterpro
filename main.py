
import logging
from app import create_app

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

from app import app

if __name__ == "__main__":
    try:
        logger.info("Starting application...")
        port = int(os.environ.get('PORT', 5000))
        debug = bool(os.environ.get('FLASK_DEBUG', True))
        app.run(host='0.0.0.0', port=port, debug=debug)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
    raise
