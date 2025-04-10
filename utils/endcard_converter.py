import os
import logging
from flask import render_template

logger = logging.getLogger(__name__)

def convert_to_endcard(file_path, filename):
    """
    Convert an uploaded image or video file into HTML endcards in both portrait and landscape formats.
    
    This is a placeholder for the user's existing convertToEndcard() logic.
    The user is expected to replace this with their actual implementation.
    
    Args:
        file_path (str): Path to the uploaded file
        filename (str): Original filename of the uploaded file
        
    Returns:
        tuple: (portrait_html, landscape_html) - HTML content for both endcard formats
    """
    logger.debug(f"Converting {file_path} to endcards")
    
    # Get file extension to determine if it's an image or video
    file_extension = os.path.splitext(filename)[1].lower()
    is_video = file_extension in ['.mp4']
    
    # Base filename without extension
    base_filename = os.path.splitext(filename)[0]
    
    # Generate portrait endcard (9:16 aspect ratio)
    portrait_html = render_template(
        'endcard_template_portrait.html',
        filename=filename,
        base_filename=base_filename,
        file_path=file_path,
        is_video=is_video
    )
    
    # Generate landscape endcard (16:9 aspect ratio)
    landscape_html = render_template(
        'endcard_template_landscape.html',
        filename=filename,
        base_filename=base_filename,
        file_path=file_path,
        is_video=is_video
    )
    
    return portrait_html, landscape_html
