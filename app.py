import os
import logging
import uuid
import base64
from flask import Flask, request, render_template, send_file, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from functools import wraps
import io

def no_size_limit(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.content_length and request.content_length > app.config['MAX_CONTENT_LENGTH']:
            request.content_length = None
        return f(*args, **kwargs)
    return wrapper
from utils.endcard_converter import convert_to_endcard
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure file upload settings
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4'}
MAX_FILE_SIZE = 2.2 * 1024 * 1024  # 2.2MB per file
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB total request size (for both files combined)

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database configuration
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Fix for PostgreSQL URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback for development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///endcards.db'

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Import and initialize the database
from models import db, Endcard, User
db.init_app(app)

# Create all database tables
with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    """Display history of all endcard conversions"""
    endcards = Endcard.query.order_by(Endcard.created_at.desc()).all()
    return render_template('history.html', endcards=endcards)

@app.route('/upgrade')
def upgrade():
    """Display the upgrade page for premium features"""
    return render_template('upgrade.html')

@app.route('/upload/combined', methods=['POST'])
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
        if not replit_user_id:
            return jsonify({'error': 'Please login to use this service'}), 401
            
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
    
    # Process the uploaded file (we only need one file now)
    for field_name in ['media_file', 'portrait_file', 'landscape_file']:  # Support multiple field names for compatibility
        if field_name in request.files:
            uploaded_file = request.files[field_name]
            
            if uploaded_file and uploaded_file.filename != '':
                # Validate file type
                if not allowed_file(uploaded_file.filename):
                    return jsonify({'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
                
                try:
                    # Check file size before saving
                    uploaded_file.seek(0, os.SEEK_END)
                    file_size = uploaded_file.tell()
                    uploaded_file.seek(0)  # Reset file pointer
                    
                    if file_size > MAX_FILE_SIZE:
                        return jsonify({'error': f'File exceeds the 2.2MB size limit (size: {file_size/1024/1024:.2f}MB)'}), 400
                    
                    # Generate a unique ID for this upload
                    upload_id = str(uuid.uuid4())
                    
                    # Save the file temporarily
                    filename = secure_filename(uploaded_file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_{filename}")
                    uploaded_file.save(file_path)
                    
                    logger.debug(f"File saved at {file_path}")
                    
                    # Determine file type and mime type
                    extension = os.path.splitext(filename)[1].lower()
                    file_type = 'video' if extension == '.mp4' else 'image'
                    mime_type = "video/mp4" if extension == '.mp4' else "image/jpeg"
                    if extension == '.png':
                        mime_type = "image/png"
                    
                    # Process both portrait and landscape files
                    portrait_file = request.files['portrait_file']
                    landscape_file = request.files['landscape_file']
                    
                    if not portrait_file or not landscape_file:
                        return jsonify({'error': 'Both portrait and landscape files are required'}), 400
                        
                    # Save both files temporarily
                    portrait_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_portrait_{filename}")
                    landscape_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_landscape_{filename}")
                    
                    portrait_file.save(portrait_path)
                    landscape_file.save(landscape_path)
                    
                    # Read and encode both files
                    with open(portrait_path, 'rb') as f:
                        portrait_data = base64.b64encode(f.read()).decode('utf-8')
                    with open(landscape_path, 'rb') as f:
                        landscape_data = base64.b64encode(f.read()).decode('utf-8')
                        
                    # Generate endcard with both orientations
                    endcard_data = convert_to_endcard(
                        file_path,
                        filename,
                        orientation='rotatable',
                        portrait_path=portrait_path,
                        landscape_path=landscape_path
                    )
                    
                    # Clean up temporary files
                    try:
                        os.remove(portrait_path)
                        os.remove(landscape_path)
                    except Exception as e:
                        logger.error(f"Error removing temporary files: {e}")
                    
                    # Update endcard record
                    endcard.portrait_filename = filename
                    endcard.portrait_file_type = file_type
                    endcard.portrait_file_size = file_size
                    endcard.portrait_created = True
                    
                    endcard.landscape_filename = filename
                    endcard.landscape_file_type = file_type
                    endcard.landscape_file_size = file_size
                    endcard.landscape_created = True
                    
                    # Store file info for response
                    file_info = {
                        'filename': filename,
                        'type': file_type,
                        'size': file_size
                    }
                    
                    # Set response data
                    rotatable_html = endcard_data['rotatable']
                    
                    # Clean up temporary file
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.error(f"Error removing temporary file: {e}")
                    
                    # We found a file, no need to check other field names
                    break
                    
                except Exception as e:
                    logger.error(f"Error processing file: {e}")
                    return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    # Save the updated endcard record
    db.session.commit()
    
    # Check if a file was processed
    if not rotatable_html:
        return jsonify({'error': 'No file was provided for conversion'}), 400
        
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
    # Allow 'rotatable' in addition to portrait and landscape
    if orientation not in ['portrait', 'landscape', 'rotatable']:
        return jsonify({'error': 'Invalid orientation'}), 400
    
    html_content = request.form.get('html')
    if not html_content:
        return jsonify({'error': 'HTML content not provided'}), 400
    
    try:
        base_filename = secure_filename(filename.rsplit('.', 1)[0])
        
        # Use 'endcard' as the suffix for rotatable HTML files
        if orientation == 'rotatable':
            output_filename = f"{base_filename}_endcard.html"
        else:
            output_filename = f"{base_filename}_{orientation}.html"
        
        encoded_content = html_content.encode('utf-8')
        buffer = io.BytesIO(encoded_content)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='text/html; charset=utf-8',
            as_attachment=True,
            download_name=output_filename,
            etag=False,
            conditional=False,
            add_etags=False
        )
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': 'Failed to generate download'}), 500

# Error handler for file too large
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 2.2MB'}), 413

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
