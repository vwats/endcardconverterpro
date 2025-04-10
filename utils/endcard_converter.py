import os
import logging
import base64
from flask import render_template

logger = logging.getLogger(__name__)

def convert_to_endcard(file_path, filename, orientation='rotatable'):
    """
    Convert an uploaded image or video file into a rotatable HTML endcard.
    
    This implementation embeds the media file as base64 in the HTML, based on the provided converter code.
    
    Args:
        file_path (str): Path to the uploaded file
        filename (str): Original filename of the uploaded file
        orientation (str): 'rotatable', 'portrait', 'landscape', or 'both' (for backwards compatibility)
        
    Returns:
        str or tuple: HTML content for the requested orientation(s)
                     If orientation='rotatable', returns a single rotatable HTML endcard
                     If orientation='both', returns (portrait_html, landscape_html) for backwards compatibility
                     If orientation='portrait', returns portrait_html for backwards compatibility
                     If orientation='landscape', returns landscape_html for backwards compatibility
    """
    logger.debug(f"Converting {file_path} to endcard, orientation: {orientation}")
    
    # Get file extension to determine if it's an image or video
    file_extension = os.path.splitext(filename)[1].lower()
    is_video = file_extension in ['.mp4']
    
    # Base filename without extension
    base_filename = os.path.splitext(filename)[0]
    
    # Read and encode the file as base64
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
            base64_data = base64.b64encode(file_data).decode('utf-8')
            logger.debug(f"Successfully encoded {filename} as base64")
    except Exception as e:
        logger.error(f"Error encoding file as base64: {e}")
        raise
    
    # Get mime type based on file extension
    mime_type = "video/mp4" if is_video else "image/jpeg"
    if file_extension == '.png':
        mime_type = "image/png"
    
    # Generate rotatable HTML (new default behavior)
    if orientation == 'rotatable':
        return generate_rotatable_html(
            base64_data, mime_type, is_video, base_filename
        )
    
    # Support for backwards compatibility with legacy code
    if orientation == 'portrait' or orientation == 'both':
        portrait_html = generate_html_with_orientation_detection(
            base64_data, mime_type, is_video, base_filename, 'portrait'
        )
    else:
        portrait_html = None
        
    if orientation == 'landscape' or orientation == 'both':
        landscape_html = generate_html_with_orientation_detection(
            base64_data, mime_type, is_video, base_filename, 'landscape'
        )
    else:
        landscape_html = None
    
    # Return based on requested orientation (for backwards compatibility)
    if orientation == 'both':
        return portrait_html, landscape_html
    elif orientation == 'portrait':
        return portrait_html
    elif orientation == 'landscape':
        return landscape_html

def generate_rotatable_html(base64_data, mime_type, is_video, base_filename):
    """
    Generate a rotatable HTML endcard with the embedded base64 media file.
    
    Args:
        base64_data (str): Base64 encoded media data
        mime_type (str): MIME type of the media (image/jpeg, image/png, video/mp4)
        is_video (bool): Whether the media is a video
        base_filename (str): Original filename without extension
        
    Returns:
        str: HTML content with embedded media and rotation capability
    """
    # Create data URL for the media
    data_url = f"data:{mime_type};base64,{base64_data}"
    
    # Use the new rotatable template
    html = render_template(
        'endcard_template_rotatable.html',
        base_filename=base_filename,
        is_video=is_video,
        data_url=data_url
    )
    
    return html

def generate_html_with_orientation_detection(base64_data, mime_type, is_video, base_filename, orientation):
    """
    Generate HTML with the embedded base64 media file.
    This is maintained for backwards compatibility.
    
    Args:
        base64_data (str): Base64 encoded media data
        mime_type (str): MIME type of the media (image/jpeg, image/png, video/mp4)
        is_video (bool): Whether the media is a video
        base_filename (str): Original filename without extension
        orientation (str): 'portrait' or 'landscape'
        
    Returns:
        str: HTML content with embedded media
    """
    # Create data URL for the media
    data_url = f"data:{mime_type};base64,{base64_data}"
    
    # Use appropriate template based on orientation
    html = render_template(
        f'endcard_template_{orientation}.html',
        base_filename=base_filename,
        is_video=is_video,
        data_url=data_url
    )
    
    return html
