import os
import logging
import uuid
from flask import Flask, request, render_template, send_file, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
import io
from utils.endcard_converter import convert_to_endcard

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configure file upload settings
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4'}
MAX_CONTENT_LENGTH = 2.2 * 1024 * 1024  # 2.2MB

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
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
        
        # Generate endcards
        portrait_html, landscape_html = convert_to_endcard(file_path, filename)
        
        # Clean up the temporary file
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Error removing temporary file: {e}")
            
        # Return the HTML content for both formats
        return jsonify({
            'portrait': portrait_html,
            'landscape': landscape_html,
            'filename': filename
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
