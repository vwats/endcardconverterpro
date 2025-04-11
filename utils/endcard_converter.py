import os
import logging
import base64
from flask import render_template

logger = logging.getLogger(__name__)

def convert_to_endcard(file_path, filename, orientation='rotatable', portrait_path=None, landscape_path=None):
    """
    Convert an uploaded image or video file into HTML endcard(s).

    Args:
        file_path (str): Path to the uploaded file
        filename (str): Original filename of the uploaded file
        orientation (str): 'rotatable', 'portrait', 'landscape', or 'both'
        portrait_path (str, optional): Path to the portrait file
        landscape_path (str, optional): Path to the landscape file

    Returns:
        dict or str: For rotatable orientation, returns dict with both portrait and landscape HTML
                    For other orientations, returns HTML string or tuple as before
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

    # Read and encode both files
    try:
        with open(portrait_path, 'rb') as f:
            portrait_data = base64.b64encode(f.read()).decode('utf-8')
        with open(landscape_path, 'rb') as f:
            landscape_data = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding files as base64: {e}")
        raise

    # Generate both portrait and landscape HTML for rotatable endcards
    if orientation == 'rotatable':
        portrait_html = generate_html_with_orientation_detection(
            portrait_data, mime_type, is_video, base_filename, 'portrait'
        )
        landscape_html = generate_html_with_orientation_detection(
            landscape_data, mime_type, is_video, base_filename, 'landscape'
        )
        return {
            'portrait': portrait_html,
            'landscape': landscape_html,
            'rotatable': generate_rotatable_html(
                portrait_data=portrait_data,
                landscape_data=landscape_data,
                portrait_mime=mime_type,
                landscape_mime=mime_type,
                is_video=is_video,
                base_filename=base_filename
            )
        }

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

def generate_rotatable_html(portrait_data, landscape_data, portrait_mime, landscape_mime, is_video, base_filename):
    """
    Generate a rotatable HTML endcard with both portrait and landscape embedded media.

    Args:
        portrait_data (str): Base64 encoded portrait media data
        landscape_data (str): Base64 encoded landscape media data
        portrait_mime (str): MIME type of the portrait media
        landscape_mime (str): MIME type of the landscape media
        is_video (bool): Whether the media is video
        base_filename (str): Original filename without extension

    Returns:
        str: HTML content with embedded media and rotation capability
    """
    # Create data URLs for both orientations
    portrait_url = f"data:{portrait_mime};base64,{portrait_data}"
    landscape_url = f"data:{landscape_mime};base64,{landscape_data}"

    # Use the rotatable template with both URLs
    html = render_template(
        'endcard_template_rotatable.html',
        base_filename=base_filename,
        is_video=is_video,
        portrait_data_url=portrait_url,
        landscape_data_url=landscape_url
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