import os
import logging
import uuid
from flask import Flask, request, render_template, send_file, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import io
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
    """Handle combined file upload for both portrait and landscape orientations"""
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
        
    portrait_html = None
    landscape_html = None
    portrait_file_info = None
    landscape_file_info = None
    
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
    
    # Process portrait file if provided
    if 'portrait_file' in request.files:
        portrait_file = request.files['portrait_file']
        
        if portrait_file and portrait_file.filename != '':
            # Validate file type
            if not allowed_file(portrait_file.filename):
                return jsonify({'error': f'Invalid portrait file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
            
            try:
                # Check file size before saving
                portrait_file.seek(0, os.SEEK_END)
                portrait_size = portrait_file.tell()
                portrait_file.seek(0)  # Reset file pointer
                
                if portrait_size > MAX_FILE_SIZE:
                    return jsonify({'error': f'Portrait file exceeds the 2.2MB size limit (size: {portrait_size/1024/1024:.2f}MB)'}), 400
                
                # Generate a unique ID for this upload
                upload_id = str(uuid.uuid4())
                
                # Save the file temporarily
                portrait_filename = secure_filename(portrait_file.filename)
                portrait_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_{portrait_filename}")
                portrait_file.save(portrait_path)
                
                logger.debug(f"Portrait file saved at {portrait_path}")
                
                # Determine file type (image or video)
                portrait_extension = os.path.splitext(portrait_filename)[1].lower()
                portrait_type = 'video' if portrait_extension == '.mp4' else 'image'
                
                # Generate portrait endcard
                portrait_html = convert_to_endcard(portrait_path, portrait_filename, orientation='portrait')
                
                # Update endcard record with portrait info
                endcard.portrait_filename = portrait_filename
                endcard.portrait_file_type = portrait_type
                endcard.portrait_file_size = portrait_size
                endcard.portrait_created = True
                
                # Store portrait info for response
                portrait_file_info = {
                    'filename': portrait_filename,
                    'type': portrait_type,
                    'size': portrait_size
                }
                
                # Clean up temporary file
                try:
                    os.remove(portrait_path)
                except Exception as e:
                    logger.error(f"Error removing temporary portrait file: {e}")
                
            except Exception as e:
                logger.error(f"Error processing portrait file: {e}")
                return jsonify({'error': f'Error processing portrait file: {str(e)}'}), 500
    
    # Process landscape file if provided
    if 'landscape_file' in request.files:
        landscape_file = request.files['landscape_file']
        
        if landscape_file and landscape_file.filename != '':
            # Validate file type
            if not allowed_file(landscape_file.filename):
                return jsonify({'error': f'Invalid landscape file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
            
            try:
                # Check file size before saving
                landscape_file.seek(0, os.SEEK_END)
                landscape_size = landscape_file.tell()
                landscape_file.seek(0)  # Reset file pointer
                
                if landscape_size > MAX_FILE_SIZE:
                    return jsonify({'error': f'Landscape file exceeds the 2.2MB size limit (size: {landscape_size/1024/1024:.2f}MB)'}), 400
                
                # Generate a unique ID for this upload
                upload_id = str(uuid.uuid4())
                
                # Save the file temporarily
                landscape_filename = secure_filename(landscape_file.filename)
                landscape_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_{landscape_filename}")
                landscape_file.save(landscape_path)
                
                logger.debug(f"Landscape file saved at {landscape_path}")
                
                # Determine file type (image or video)
                landscape_extension = os.path.splitext(landscape_filename)[1].lower()
                landscape_type = 'video' if landscape_extension == '.mp4' else 'image'
                
                # Generate landscape endcard
                landscape_html = convert_to_endcard(landscape_path, landscape_filename, orientation='landscape')
                
                # Update endcard record with landscape info
                endcard.landscape_filename = landscape_filename
                endcard.landscape_file_type = landscape_type
                endcard.landscape_file_size = landscape_size
                endcard.landscape_created = True
                
                # Store landscape info for response
                landscape_file_info = {
                    'filename': landscape_filename,
                    'type': landscape_type,
                    'size': landscape_size
                }
                
                # Clean up temporary file
                try:
                    os.remove(landscape_path)
                except Exception as e:
                    logger.error(f"Error removing temporary landscape file: {e}")
                
            except Exception as e:
                logger.error(f"Error processing landscape file: {e}")
                return jsonify({'error': f'Error processing landscape file: {str(e)}'}), 500
    
    # Save the updated endcard record
    db.session.commit()
    
    # Check if at least one file was processed
    if not portrait_html and not landscape_html:
        return jsonify({'error': 'No files were provided for conversion'}), 400
        
    # Deduct credit after successful conversion
    user.credits -= 1
    db.session.commit()
    
    # Return the HTML content and file info
    response = {
        'endcard_id': endcard.id
    }
    
    if portrait_html:
        response['portrait'] = portrait_html
        response['portrait_info'] = portrait_file_info
    
    if landscape_html:
        response['landscape'] = landscape_html
        response['landscape_info'] = landscape_file_info
    
    # Convert HTML content to a safe JSON format
    if portrait_html:
        response['portrait'] = str(portrait_html)
    if landscape_html:
        response['landscape'] = str(landscape_html)
    return jsonify(response)

@app.route('/download/<orientation>/<filename>', methods=['GET', 'POST'])
def download_endcard(orientation, filename):
    if orientation not in ['portrait', 'landscape']:
        return jsonify({'error': 'Invalid orientation'}), 400
    
    html_content = request.form.get('html')
    if not html_content:
        return jsonify({'error': 'HTML content not provided'}), 400
    
    try:
        base_filename = secure_filename(filename.rsplit('.', 1)[0])
        output_filename = f"{base_filename}_{orientation}.html"
        
        return Response(
            html_content,
            mimetype='text/html',
            headers={
                "Content-Disposition": f"attachment;filename={output_filename}",
                "Content-Type": "text/html; charset=utf-8"
            }
        )

# Error handler for file too large
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 2.2MB'}), 413

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
