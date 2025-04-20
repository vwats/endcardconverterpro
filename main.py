import logging
from app import create_app

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

logger.debug("Starting application initialization...")
app = create_app()

if __name__ == "__main__":
    logger.info("Configuring application...")
    app.config['PROPAGATE_EXCEPTIONS'] = True
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    logger.info("Starting application on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)