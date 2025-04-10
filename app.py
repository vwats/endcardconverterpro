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
MAX_CONTENT_LENGTH = 2.2 * 1024 * 1024  # 2.2MB

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
from models import db, Endcard
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

@app.route('/upload/portrait', methods=['POST'])
def upload_portrait():
    """Handle portrait-oriented file upload"""
    # Check if there's a file in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # Check if a file was selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file type
    if not allowed_file(file.filename):
        return jsonify({'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    try:
        # Generate a unique ID for this upload
        upload_id = str(uuid.uuid4())
        
        # Save the file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_{filename}")
        file.save(file_path)
        
        logger.debug(f"File saved at {file_path}")
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Determine file type (image or video)
        file_extension = os.path.splitext(filename)[1].lower()
        file_type = 'video' if file_extension == '.mp4' else 'image'
        
        # Generate portrait endcard only
        portrait_html = convert_to_endcard(file_path, filename, orientation='portrait')
        
        # Check if we need to create a new record or update an existing one
        endcard_id = request.form.get('endcard_id')
        
        if endcard_id and endcard_id.isdigit():
            # Update existing record
            endcard = Endcard.query.get(int(endcard_id))
            if endcard:
                endcard.portrait_filename = filename
                endcard.portrait_file_type = file_type
                endcard.portrait_file_size = file_size
                endcard.portrait_created = bool(portrait_html)
                db.session.commit()
            else:
                # Create new record if ID not found
                endcard = Endcard(
                    portrait_filename=filename,
                    portrait_file_type=file_type,
                    portrait_file_size=file_size,
                    portrait_created=bool(portrait_html)
                )
                db.session.add(endcard)
                db.session.commit()
        else:
            # Create new record
            endcard = Endcard(
                portrait_filename=filename,
                portrait_file_type=file_type,
                portrait_file_size=file_size,
                portrait_created=bool(portrait_html)
            )
            db.session.add(endcard)
            db.session.commit()
        
        # Clean up the temporary file
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error removing temporary file: {e}")
            
        # Return the HTML content
        return jsonify({
            'portrait': portrait_html,
            'filename': filename,
            'endcard_id': endcard.id
        })
    
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/upload/landscape', methods=['POST'])
def upload_landscape():
    """Handle landscape-oriented file upload"""
    # Check if there's a file in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # Check if a file was selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file type
    if not allowed_file(file.filename):
        return jsonify({'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    try:
        # Generate a unique ID for this upload
        upload_id = str(uuid.uuid4())
        
        # Save the file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_{filename}")
        file.save(file_path)
        
        logger.debug(f"File saved at {file_path}")
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Determine file type (image or video)
        file_extension = os.path.splitext(filename)[1].lower()
        file_type = 'video' if file_extension == '.mp4' else 'image'
        
        # Generate landscape endcard only
        landscape_html = convert_to_endcard(file_path, filename, orientation='landscape')
        
        # Check if we need to create a new record or update an existing one
        endcard_id = request.form.get('endcard_id')
        
        if endcard_id and endcard_id.isdigit():
            # Update existing record
            endcard = Endcard.query.get(int(endcard_id))
            if endcard:
                endcard.landscape_filename = filename
                endcard.landscape_file_type = file_type
                endcard.landscape_file_size = file_size
                endcard.landscape_created = bool(landscape_html)
                db.session.commit()
            else:
                # Create new record if ID not found
                endcard = Endcard(
                    landscape_filename=filename,
                    landscape_file_type=file_type,
                    landscape_file_size=file_size,
                    landscape_created=bool(landscape_html)
                )
                db.session.add(endcard)
                db.session.commit()
        else:
            # Create new record
            endcard = Endcard(
                landscape_filename=filename,
                landscape_file_type=file_type,
                landscape_file_size=file_size,
                landscape_created=bool(landscape_html)
            )
            db.session.add(endcard)
            db.session.commit()
        
        # Clean up the temporary file
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error removing temporary file: {e}")
            
        # Return the HTML content
        return jsonify({
            'landscape': landscape_html,
            'filename': filename,
            'endcard_id': endcard.id
        })
    
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/download/<orientation>/<filename>')
def download_endcard(orientation, filename):
    if orientation not in ['portrait', 'landscape']:
        return jsonify({'error': 'Invalid orientation'}), 400
    
    # Get the HTML content from the request
    html_content = request.args.get('html')
    
    if not html_content:
        return jsonify({'error': 'HTML content not provided'}), 400
    
    base_filename = secure_filename(filename.rsplit('.', 1)[0])
    output_filename = f"{base_filename}_{orientation}.html"
    
    # Create a file-like object
    file_obj = io.BytesIO(html_content.encode('utf-8'))
    
    return send_file(
        file_obj,
        as_attachment=True,
        download_name=output_filename,
        mimetype='text/html'
    )

# Error handler for file too large
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 2.2MB'}), 413

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
