"""Utility functions for file handling and data processing."""

import base64
import os
import mimetypes
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def encode_pdf_to_base64(pdf_path: str) -> str:
    """
    Encode a PDF file to base64 string.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Base64 encoded string of the PDF
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        ValueError: If the file is too large (>20MB)
        IOError: If there's an error reading the file
    """
    # Check if file exists
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Check file size (20MB limit for inline data)
    file_size = os.path.getsize(pdf_path)
    max_size = 20 * 1024 * 1024  # 20MB in bytes
    
    if file_size > max_size:
        raise ValueError(f"PDF file too large: {file_size} bytes. Maximum allowed: {max_size} bytes (20MB)")
    
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_bytes = pdf_file.read()
            base64_string = base64.b64encode(pdf_bytes).decode('utf-8')
            
        logger.info(f"Successfully encoded PDF to base64: {pdf_path} ({file_size} bytes)")
        return base64_string
        
    except Exception as e:
        logger.error(f"Error encoding PDF to base64: {e}")
        raise IOError(f"Failed to read and encode PDF file: {e}")


def validate_file_path(file_path: str, expected_extension: Optional[str] = None) -> bool:
    """
    Validate if a file path exists and optionally has the expected extension.
    
    Args:
        file_path: Path to the file
        expected_extension: Expected file extension (e.g., '.pdf')
        
    Returns:
        True if valid, False otherwise
    """
    if not os.path.exists(file_path):
        logger.warning(f"File does not exist: {file_path}")
        return False
    
    if expected_extension and not file_path.lower().endswith(expected_extension.lower()):
        logger.warning(f"File does not have expected extension {expected_extension}: {file_path}")
        return False
    
    return True


def get_file_info(file_path: str) -> dict:
    """
    Get information about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    
    stat = os.stat(file_path)
    return {
        "path": file_path,
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "exists": True,
        "is_readable": os.access(file_path, os.R_OK)
    }


# Supported MIME types for Vertex AI File API
SUPPORTED_MIME_TYPES = {
    # Documents
    'application/pdf': {'type': 'document', 'max_size_mb': 20},
    'text/plain': {'type': 'document', 'max_size_mb': 20},
    #'application/vnd.openxmlformats-officedocument.wordprocessingml.document': {'type': 'document', 'max_size_mb': 20},
    'application/msword': {'type': 'document', 'max_size_mb': 20},
    #'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': {'type': 'spreadsheet', 'max_size_mb': 20},
    'application/vnd.ms-excel': {'type': 'spreadsheet', 'max_size_mb': 20},
    'text/csv': {'type': 'spreadsheet', 'max_size_mb': 20},
    #'application/vnd.openxmlformats-officedocument.presentationml.presentation': {'type': 'presentation', 'max_size_mb': 20},
    'application/vnd.ms-powerpoint': {'type': 'presentation', 'max_size_mb': 20},
    
    # Images
    'image/png': {'type': 'image', 'max_size_mb': 20},
    'image/jpeg': {'type': 'image', 'max_size_mb': 20},
    'image/gif': {'type': 'image', 'max_size_mb': 20},
    'image/webp': {'type': 'image', 'max_size_mb': 20},
    
    # Audio
    'audio/mpeg': {'type': 'audio', 'max_size_mb': 20},
    'audio/wav': {'type': 'audio', 'max_size_mb': 20},
    'audio/mp4': {'type': 'audio', 'max_size_mb': 20},
    'audio/ogg': {'type': 'audio', 'max_size_mb': 20},
    
    # Video
    'video/mp4': {'type': 'video', 'max_size_mb': 20},
    'video/quicktime': {'type': 'video', 'max_size_mb': 20},
    'video/webm': {'type': 'video', 'max_size_mb': 20},
    'video/avi': {'type': 'video', 'max_size_mb': 20},
}


def get_mime_type(file_path: str) -> Optional[str]:
    """
    Detect MIME type from file path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string or None if not detected
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    print(mime_type)
    return mime_type


def is_supported_mime_type(mime_type: str) -> bool:
    """
    Check if MIME type is supported by Vertex AI.
    
    Args:
        mime_type: MIME type to check
        
    Returns:
        True if supported, False otherwise
    """
    return mime_type in SUPPORTED_MIME_TYPES


def get_file_type_info(mime_type: str) -> Optional[Dict]:
    """
    Get file type information for a MIME type.
    
    Args:
        mime_type: MIME type
        
    Returns:
        Dictionary with type info or None if not supported
    """
    return SUPPORTED_MIME_TYPES.get(mime_type)


def encode_file_to_base64(file_path: str, mime_type: Optional[str] = None) -> str:
    """
    Encode any supported file type to base64 string.
    
    Args:
        file_path: Path to the file
        mime_type: MIME type (optional, will be detected if not provided)
        
    Returns:
        Base64 encoded string of the file
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file type is not supported or file is too large
        IOError: If there's an error reading the file
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Detect MIME type if not provided
    if mime_type is None:
        mime_type = get_mime_type(file_path)
        if mime_type is None:
            raise ValueError(f"Could not detect MIME type for file: {file_path}")
    
    # Check if MIME type is supported
    if not is_supported_mime_type(mime_type):
        raise ValueError(f"Unsupported MIME type: {mime_type}")
    
    # Check file size
    file_size = os.path.getsize(file_path)
    type_info = get_file_type_info(mime_type)
    max_size = type_info['max_size_mb'] * 1024 * 1024  # Convert MB to bytes
    
    if file_size > max_size:
        raise ValueError(f"File too large: {file_size} bytes. Maximum allowed for {mime_type}: {max_size} bytes ({type_info['max_size_mb']}MB)")
    
    try:
        with open(file_path, 'rb') as file:
            file_bytes = file.read()
            base64_string = base64.b64encode(file_bytes).decode('utf-8')
            
        logger.info(f"Successfully encoded {mime_type} file to base64: {file_path} ({file_size} bytes)")
        return base64_string
        
    except Exception as e:
        logger.error(f"Error encoding file to base64: {e}")
        raise IOError(f"Failed to read and encode file: {e}")


def validate_file_for_analysis(file_path: str, mime_type: Optional[str] = None) -> Dict:
    """
    Validate file for AI analysis.
    
    Args:
        file_path: Path to the file
        mime_type: MIME type (optional, will be detected if not provided)
        
    Returns:
        Dictionary with validation results
    """
    result = {
        'valid': False,
        'mime_type': mime_type,
        'file_type': None,
        'size_mb': 0,
        'errors': []
    }
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            result['errors'].append("File does not exist")
            return result
        
        # Get file info
        file_info = get_file_info(file_path)
        result['size_mb'] = file_info['size_mb']
        
        # Detect MIME type if not provided
        if mime_type is None:
            mime_type = get_mime_type(file_path)
            result['mime_type'] = mime_type
            
        if mime_type is None:
            result['errors'].append("Could not detect file MIME type")
            return result
        
        # Check if supported
        if not is_supported_mime_type(mime_type):
            result['errors'].append(f"Unsupported MIME type: {mime_type}")
            return result
        
        # Get type info
        type_info = get_file_type_info(mime_type)
        result['file_type'] = type_info['type']
        
        # Check file size
        if file_info['size_mb'] > type_info['max_size_mb']:
            result['errors'].append(f"File too large: {file_info['size_mb']}MB (max: {type_info['max_size_mb']}MB)")
            return result
        
        # Check readability
        if not file_info['is_readable']:
            result['errors'].append("File is not readable")
            return result
        
        result['valid'] = True
        return result
        
    except Exception as e:
        result['errors'].append(f"Validation error: {str(e)}")
        return result


def get_default_prompt_for_file_type(file_type: str) -> str:
    """
    Get default analysis prompt based on file type.
    
    Args:
        file_type: Type of file (document, image, audio, video, etc.)
        
    Returns:
        Default prompt string
    """
    prompts = {
        'document': (
            "Please provide a comprehensive analysis of this document. Include:\n"
            "1. Document type and structure\n"
            "2. Key content and main topics\n"
            "3. Important data, numbers, or findings\n"
            "4. Summary of conclusions or recommendations\n"
            "5. Any notable formatting, tables, or visual elements"
        ),
        'image': (
            "Please analyze this image in detail. Describe:\n"
            "1. Overall scene and context\n"
            "2. Objects, people, and their relationships\n"
            "3. Colors, lighting, and composition\n"
            "4. Any text or written content visible\n"
            "5. Notable details or interesting elements"
        ),
        'audio': (
            "Please analyze this audio file. Provide:\n"
            "1. Transcription of spoken content\n"
            "2. Identification of speakers or voices\n"
            "3. Key topics and main points discussed\n"
            "4. Tone, mood, and context\n"
            "5. Any background sounds or music"
        ),
        'video': (
            "Please analyze this video file. Include:\n"
            "1. Description of scenes and visual content\n"
            "2. Transcription of dialogue or narration\n"
            "3. Key actions and events\n"
            "4. Visual elements (locations, people, objects)\n"
            "5. Overall narrative or message"
        ),
        'spreadsheet': (
            "Please analyze this spreadsheet data. Provide:\n"
            "1. Structure and organization of the data\n"
            "2. Key metrics and numerical insights\n"
            "3. Patterns, trends, or anomalies\n"
            "4. Summary of main data points\n"
            "5. Any formulas or calculations present"
        ),
        'presentation': (
            "Please analyze this presentation. Include:\n"
            "1. Overall theme and purpose\n"
            "2. Key points from each slide\n"
            "3. Structure and flow of content\n"
            "4. Visual elements and design\n"
            "5. Main conclusions or call-to-action"
        )
    }
    
    return prompts.get(file_type, prompts['document'])
