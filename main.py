
import logging
from app import create_app

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

try:
    logger.info("Starting application initialization...")
    app = create_app()
    
    if __name__ == "__main__":
        logger.info("Running in __main__, configuring application...")
        app.config['PROPAGATE_EXCEPTIONS'] = True
        app.config['PREFERRED_URL_SCHEME'] = 'https' if os.environ.get('PRODUCTION') else 'http'
        port = int(os.environ.get('PORT', 5000))
        debug = bool(os.environ.get('FLASK_DEBUG', True))
        logger.info(f"Starting application on port {port} with debug={debug}...")
        app.run(host='0.0.0.0', port=port, debug=debug)
        app.run(host='0.0.0.0', port=5000, debug=True)
except Exception as e:
    logger.error(f"Failed to start application: {str(e)}", exc_info=True)
    raise
