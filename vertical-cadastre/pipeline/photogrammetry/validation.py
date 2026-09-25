import os
from typing import List, Tuple
from pipeline.utils.logger import get_logger

logger = get_logger("PhotogrammetryValidation")

SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}

def validate_input_directory(directory: str, min_images: int = 3) -> Tuple[bool, str, List[str]]:
    """
    Validates a directory contains a valid image dataset for photogrammetry.
    Returns: (is_valid, error_message, list_of_valid_images)
    """
    if not os.path.exists(directory):
        msg = f"Directory does not exist: {directory}"
        logger.error(msg)
        return False, msg, []
        
    if not os.path.isdir(directory):
        msg = f"Path is not a directory: {directory}"
        logger.error(msg)
        return False, msg, []
        
    valid_images = []
    seen_names = set()
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue
            
        ext = os.path.splitext(filename)[1].lower()
        if ext in SUPPORTED_EXTENSIONS:
            # Check for duplicates by name alone (excluding ext) to catch issues like img1.jpg and img1.png
            basename = os.path.splitext(filename)[0]
            if basename in seen_names:
                msg = f"Duplicate base filename found: {filename}"
                logger.error(msg)
                return False, msg, []
            
            seen_names.add(basename)
            valid_images.append(filepath)
            
    if len(valid_images) < min_images:
        msg = f"Insufficient images found. Required: {min_images}, Found: {len(valid_images)}"
        logger.error(msg)
        return False, msg, valid_images
        
    logger.info(f"Validated dataset: {len(valid_images)} images found.")
    return True, "", valid_images
