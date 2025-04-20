import os
import logging
import uuid
import base64
import io
from flask import Flask, request, render_template, send_file, jsonify, flash, redirect, url_for, Response, make_response
from werkzeug.utils import secure_filename
from functools import wraps
import io
from werkzeug.middleware.proxy_fix import ProxyFix
import stripe
from models import db, User, Endcard
from utils.endcard_converter import convert_to_endcard

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG if os.environ.get('FLASK_DEBUG') else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s [in %(pathname)s:%(lineno)d]'
)
logger = logging.getLogger(__name__)

# Set deployment domain if in production
if os.environ.get('PRODUCTION'):
    server_name = os.environ.get('SERVER_NAME', 'endcardconverter.com')
    logger.info(f"Running in production mode with SERVER_NAME: {server_name}")

# Log important environment variables and configuration
if os.environ.get('PRODUCTION'):
    logger.info("Running in PRODUCTION mode")
    logger.info(f"SERVER_NAME: {os.environ.get('SERVER_NAME')}")
    logger.info(f"Stripe configuration present: {bool(os.environ.get('STRIPE_SECRET_KEY'))}")

# Initialize Stripe with error handling
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
if not stripe.api_key:
    logger.error("Stripe API key is not configured")
else:
    logger.info("Stripe API key is configured")

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        if os.environ.get('PRODUCTION'):
            response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: *.stripe.com *.stripe.network"
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    # Configure file upload settings
    UPLOAD_FOLDER = '/tmp/uploads'
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4'}
    MAX_FILE_SIZE = 2.2 * 1024 * 1024
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # Create upload folder if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///endcards.db'

    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Increase to 16MB

    # Initialize extensions
    db.init_app(app)

    # Create tables within app context
    with app.app_context():
        db.create_all()

    def no_size_limit(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.content_length and request.content_length > app.config['MAX_CONTENT_LENGTH']:
                request.content_length = None
            return f(*args, **kwargs)
        return wrapper

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    # Register routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/history')
    def history():
        endcards = Endcard.query.order_by(Endcard.created_at.desc()).all()
        return render_template('history.html', endcards=endcards)

    @app.route('/upgrade')
    def upgrade():
        try:
            stripe_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
            if not stripe_key:
                logger.error("STRIPE_PUBLISHABLE_KEY is missing")
                return "Stripe configuration error: Missing publishable key", 500

            if not stripe.api_key:
                logger.error("STRIPE_SECRET_KEY is missing")
                return "Stripe configuration error: Missing secret key", 500

            return render_template('upgrade.html', stripe_key=stripe_key)
        except Exception as e:
            logger.error(f"Error rendering upgrade page: {str(e)}")
            return str(e), 500

    @app.route('/upload/combined', methods=['POST'])
    @no_size_limit
    def upload_combined():
        """Handle file upload for rotatable HTML endcard"""
        # Skip login check if in development mode
        if not os.environ.get('PRODUCTION'):
            user = User.query.first()
            if not user:
                user = User(replit_id='dev', credits=999)
                db.session.add(user)
                db.session.commit()
        else:
            # Check if user is logged in and has credits
            replit_user_id = request.headers.get('X-Replit-User-Id')
            logger.info("Auth attempt - Headers received: %s", dict(request.headers))

            if not replit_user_id:
                logger.error("Authentication failed - No X-Replit-User-Id header")
                return jsonify({'error': 'User not authenticated. Please ensure you are logged into Replit.'}), 401

            user = User.query.filter_by(replit_id=replit_user_id).first()
            if not user:
                # Create new user with 1 free credit
                user = User(replit_id=replit_user_id)
                db.session.add(user)
                db.session.commit()

            if user.credits <= 0:
                return jsonify({'error': 'No credits remaining. Please upgrade to continue using the service.'}), 402

        rotatable_html = None
        file_info = None

        # Check for existing endcard ID
        endcard_id = request.form.get('endcard_id')

        # Create a new endcard record or retrieve an existing one
        if endcard_id and endcard_id.isdigit():
            endcard = Endcard.query.get(int(endcard_id))
            if not endcard:
                endcard = Endcard()
                db.session.add(endcard)
                db.session.commit()
        else:
            endcard = Endcard()
            db.session.add(endcard)
            db.session.commit()

        # Process portrait and landscape files
        portrait_file = request.files.get('portrait_file')
        landscape_file = request.files.get('landscape_file')
        temp_files = []

        try:
            if not portrait_file or not landscape_file:
                return jsonify({'error': 'Both portrait and landscape files are required'}), 400

            for upload_file in [portrait_file, landscape_file]:
                if not upload_file.filename:
                    return jsonify({'error': 'Empty filename provided'}), 400

                if not allowed_file(upload_file.filename):
                    return jsonify({'error': f'Invalid file type for {upload_file.filename}. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

                # Check file size
                upload_file.seek(0, os.SEEK_END)
                file_size = upload_file.tell()
                upload_file.seek(0)

                if file_size > MAX_FILE_SIZE:
                    return jsonify({'error': f'File {upload_file.filename} exceeds 2.2MB limit (size: {file_size/1024/1024:.2f}MB)'}), 400

            # If validation passes, save files
            upload_id = str(uuid.uuid4())

            # Save files with unique names
            portrait_filename = secure_filename(portrait_file.filename)
            landscape_filename = secure_filename(landscape_file.filename)

            portrait_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_portrait_{portrait_filename}")
            landscape_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_landscape_{landscape_filename}")

            portrait_file.save(portrait_path)
            landscape_file.save(landscape_path)

            temp_files.extend([portrait_path, landscape_path])

            # Determine file type and mime type
            extension = os.path.splitext(portrait_filename)[1].lower()
            file_type = 'video' if extension == '.mp4' else 'image'
            mime_type = "video/mp4" if extension == '.mp4' else "image/jpeg"
            if extension == '.png':
                mime_type = "image/png"

            # Process both portrait and landscape files (redundant code removed)

            # Read and encode both files
            with open(portrait_path, 'rb') as f:
                portrait_data = base64.b64encode(f.read()).decode('utf-8')
            with open(landscape_path, 'rb') as f:
                landscape_data = base64.b64encode(f.read()).decode('utf-8')

            # Generate endcard with both orientations
            endcard_data = convert_to_endcard(
                portrait_path,
                portrait_filename,
                orientation='rotatable',
                portrait_path=portrait_path,
                landscape_path=landscape_path
            )

            # Update endcard record with both files
            endcard.portrait_filename = portrait_filename
            endcard.portrait_file_type = 'video' if portrait_filename.endswith('.mp4') else 'image'
            endcard.portrait_file_size = os.path.getsize(portrait_path)
            endcard.portrait_created = True

            endcard.landscape_filename = landscape_filename
            endcard.landscape_file_type = 'video' if landscape_filename.endswith('.mp4') else 'image'
            endcard.landscape_file_size = os.path.getsize(landscape_path)
            endcard.landscape_created = True

            # Store file info for response
            file_info = {
                            'portrait': {'filename': portrait_filename, 'size': endcard.portrait_file_size},
                            'landscape': {'filename': landscape_filename, 'size': endcard.landscape_file_size}
                        }
        except IOError as e:
            logger.error(f"IO Error processing files: {e}")
            return jsonify({'error': 'Failed to process uploaded files'}), 500
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return jsonify({'error': 'An unexpected error occurred'}), 500
        finally:
            # Clean up all temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    logger.error(f"Failed to remove temporary file {temp_file}: {e}")

        # Set response data
        rotatable_html = endcard_data['rotatable']


        # Deduct credit after successful conversion
        user.credits -= 1
        db.session.commit()

        # Return the HTML content and file info
        response = {
            'endcard_id': endcard.id,
            'html': str(rotatable_html),
            'file_info': file_info
        }

        # For backward compatibility
        response['portrait'] = str(rotatable_html)
        response['portrait_info'] = file_info
        response['landscape'] = str(rotatable_html)
        response['landscape_info'] = file_info

        return jsonify(response)

    @app.route('/download/<orientation>/<filename>', methods=['POST'])
    @no_size_limit
    def download_endcard(orientation, filename):
        logger.debug(f"Download request for {orientation} orientation, filename: {filename}")

        if orientation not in ['portrait', 'landscape', 'rotatable']:
            logger.error(f"Invalid orientation requested: {orientation}")
            return jsonify({'error': 'Invalid orientation'}), 400

        try:
            if request.content_type and 'multipart/form-data' in request.content_type:
                html_content = request.form.get('html')
            else:
                html_content = request.get_data().decode('utf-8')

            if not html_content:
                logger.error("No HTML content provided in request")
                return jsonify({'error': 'HTML content not provided'}), 400

            logger.debug(f"Content size: {len(html_content)} bytes")
            logger.debug(f"Content type: {request.content_type}")

            # Strip any path and get just the filename
            original_filename = filename.split('/')[-1]
            # Remove "endcard_" prefix if it exists
            if original_filename.startswith('endcard_'):
                original_filename = original_filename[8:]
            # Remove any existing extension
            original_filename = original_filename.rsplit('.', 1)[0]
            output_filename = f"{original_filename}_endcard.html"

            logger.info(f"Processing download for {output_filename}")
            logger.debug(f"HTML content size: {len(html_content)} bytes")

            encoded_content = html_content.encode('utf-8')
            buffer = io.BytesIO(encoded_content)
            buffer.seek(0)

            response = send_file(
                buffer,
                mimetype='text/html',
                as_attachment=True,
                download_name=output_filename,
                max_age=0
            )

            logger.debug("Successfully created response")
            return response

        except Exception as e:
            logger.error(f"Download failed: {str(e)}", exc_info=True)
            return jsonify({'error': f"Download failed: {str(e)}"}), 500

    # Error handler for file too large
    @app.route('/debug/headers')
    def debug_headers():
        """Check if security headers are blocking downloads"""
        response = jsonify({
            'user_agent': request.headers.get('User-Agent'),
            'content_security_policy': request.headers.get('Content-Security-Policy'),
            'content_disposition': request.headers.get('Content-Disposition'),
            'download_headers': {
                'x-content-type-options': request.headers.get('X-Content-Type-Options'),
                'x-frame-options': request.headers.get('X-Frame-Options')
            }
        })
        response.headers.add("Content-Security-Policy", "default-src 'self'")
        return response

    @app.route('/create-checkout-session', methods=['POST', 'OPTIONS'])
    def create_checkout_session():
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response

        # Generate temporary user ID for guest checkout
        replit_user_id = request.headers.get('X-Replit-User-Id', str(uuid.uuid4()))

        package = request.form.get('package')
        if not package:
            return jsonify({'error': 'No package specified'}), 400

        if package not in ['starter', 'standard', 'pro']:
            return jsonify({'error': 'Invalid package selected'}), 400

        try:
            # Debug: Print environment variables
            logger.debug(f"STRIPE_SECRET_KEY set: {'Yes' if stripe.api_key else 'No'}")
            logger.debug(f"STRIPE_PRICE_ID_STARTER: {os.environ.get('STRIPE_PRICE_ID_STARTER')}")
            logger.debug(f"STRIPE_PRICE_ID_STANDARD: {os.environ.get('STRIPE_PRICE_ID_STANDARD')}")
            logger.debug(f"STRIPE_PRICE_ID_PRO: {os.environ.get('STRIPE_PRICE_ID_PRO')}")

            stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
            if not stripe.api_key:
                logger.error("Stripe API key is not set")
                return jsonify({'error': 'Stripe configuration error'}), 500

            # Define package prices and credits
            packages = {
                'starter': {
                    'price_id': os.environ.get('STRIPE_PRICE_ID_STARTER', 'price_1RDwmW2CWLRgle41p4sT3eTP'),
                    'credits': 10
                },
                'standard': {
                    'price_id': os.environ.get('STRIPE_PRICE_ID_STANDARD', 'price_1RDwmW2CWLRgle41pXkoV3HaL'),
                    'credits': 30
                },
                'pro': {
                    'price_id': os.environ.get('STRIPE_PRICE_ID_PRO', 'price_1RDwmW2CWLRgle41pbfyWtO0j'),
                    'credits': 60
                }
            }

            if package not in packages:
                logger.error(f"Invalid package selected: {package}")
                return jsonify({'error': 'Invalid package selected'}), 400

            # Get price ID from environment or use default
            price_id = os.environ.get(f'STRIPE_PRICE_ID_{package.upper()}', packages[package]['price_id'])

            if not price_id or not isinstance(price_id, str) or not price_id.startswith('price_'):
                logger.error(f"Invalid Stripe price ID format for {package}: {price_id}")
                return jsonify({'error': 'Invalid price configuration'}), 500

            logger.info(f"Creating checkout for package {package} with price_id {price_id}")

            logger.info(f"Creating checkout session for package: {package}")
            logger.info(f"Using price ID: {price_id}")

            if not price_id.startswith('price_'):
                logger.error(f"Invalid price ID format: {price_id}")
                return jsonify({'error': 'Invalid price ID format. Must start with "price_"'}), 400

            try:
                base_url = os.environ.get('SERVER_NAME', request.host_url.rstrip('/'))
                if not base_url.startswith(('http://', 'https://')):
                    base_url = f"https://{base_url}"

                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price': price_id,
                        'quantity': 1,
                        'adjustable_quantity': {
                            'enabled': False
                        }
                    }],
                    mode='payment',
                    success_url=f"{base_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                    cancel_url=f"{base_url}/payment/cancel",
                    metadata={
                        'replit_user_id': replit_user_id,
                        'credits': packages[package]['credits']
                    }
                )
                logger.info(f"Created checkout session {checkout_session.id} for user {replit_user_id}")
                return jsonify({'id': checkout_session.id})
            except stripe.error.StripeError as e:
                logger.error(f"Stripe error: {str(e)}")
                return jsonify({'error': str(e)}), 403
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return jsonify({'error': str(e)}), 403
        except Exception as e:
            logger.error(f"Unexpected error in checkout: {str(e)}", exc_info=True)
            return jsonify({'error': 'An unexpected error occurred'}), 500

    @app.route('/payment/success')
    def payment_success():
        session_id = request.args.get('session_id')
        if not session_id:
            flash('Invalid payment session', 'error')
            return redirect(url_for('upgrade'))

        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                user = User.query.filter_by(replit_id=session.metadata.replit_user_id).first()
                if user:
                    user.credits += int(session.metadata.credits)
                    db.session.commit()
                    flash(f'Payment successful! {session.metadata.credits} credits have been added.', 'success')
                else:
                    flash('User not found', 'error')
            else:
                flash('Payment not completed', 'error')
        except Exception as e:
            flash('Error processing payment', 'error')

        return redirect(url_for('index'))

    @app.route('/payment/cancel')
    def payment_cancel():
        flash('Payment cancelled.', 'warning')
        return redirect(url_for('upgrade'))

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'File too large. Maximum size is 2.2MB'}), 413

    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)