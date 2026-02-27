"""
exif_service.py — Centralized EXIF metadata extraction and manipulation service

This service consolidates all EXIF-related operations to eliminate code duplication
across signature_viewer.py, signing_engine.py, and verification_service.py.

Key Features:
    - Standardized EXIF data extraction
    - Profile data reconstruction from EXIF fields
    - Consistent field encoding/decoding handling
    - Unified metadata embedding logic

Author: Bernard Ennis
License: MIT
"""

import piexif
import json
from datetime import datetime
from piexif.helper import UserComment
from utils import extract_creation_datetime, normalise_strings


class EXIFService:
    """Centralized service for EXIF metadata operations."""
    
    @staticmethod
    def load_exif_safely(image_path: str) -> dict:
        """
        Load EXIF data from image with error handling.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: EXIF dictionary with standard structure
        """
        try:
            return piexif.load(image_path)
        except Exception:
            return {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
    
    @staticmethod
    def extract_xp_field(exif_dict: dict, field_id: int) -> str:
        """
        Extract and decode XP fields (XPAuthor, XPKeywords, etc.) with consistent handling.
        
        Args:
            exif_dict (dict): EXIF dictionary
            field_id (int): EXIF field ID (e.g., piexif.ImageIFD.XPAuthor)
            
        Returns:
            str: Decoded field value or empty string
        """
        if field_id not in exif_dict["0th"]:
            return ""
            
        xp_data = exif_dict["0th"][field_id]
        
        if isinstance(xp_data, tuple):
            # Convert tuple of bytes to bytes, then decode
            return bytes(xp_data).decode("utf-16le", "ignore").strip()
        elif isinstance(xp_data, bytes):
            return xp_data.decode("utf-16le", "ignore").strip()
        else:
            return str(xp_data).strip()
    
    @staticmethod
    def extract_author_field(exif_dict: dict) -> str:
        """
        Extract author from Artist field and clean email formatting.
        
        Args:
            exif_dict (dict): EXIF dictionary
            
        Returns:
            str: Clean author name without email
        """
        author_raw = exif_dict["0th"].get(piexif.ImageIFD.Artist, b"")
        if isinstance(author_raw, bytes):
            author_raw = author_raw.decode("utf-8", "ignore")
        
        author = str(author_raw).strip()
        
        # Remove email from author field if present (e.g., "Bernard Ennis <email>" -> "Bernard Ennis")
        if '<' in author and '>' in author:
            author = author.split('<')[0].strip()
            
        return author
    
    @staticmethod
    def extract_profile_from_exif(image_path: str) -> dict:
        """
        Extract complete profile data from image EXIF metadata.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Profile dictionary with author, copyright, license, year
        """
        exif_dict = EXIFService.load_exif_safely(image_path)
        
        # Extract basic author field
        author = EXIFService.extract_author_field(exif_dict)
        
        # Extract copyright holder from XPAuthor field
        copyright_holder = EXIFService.extract_xp_field(exif_dict, piexif.ImageIFD.XPAuthor)
        
        # Extract license from XPKeywords field
        license = EXIFService.extract_xp_field(exif_dict, piexif.ImageIFD.XPKeywords)
        
        # Extract year from creation datetime
        year = extract_creation_datetime(image_path).year
        
        return {
            "author": author,
            "copyright": copyright_holder,
            "license": license,
            "year": str(year)
        }
    
    @staticmethod
    def embed_profile_metadata(exif_dict: dict, profile: dict, email: str = "") -> None:
        """
        Embed profile data into EXIF dictionary with consistent encoding.
        
        Args:
            exif_dict (dict): EXIF dictionary to modify
            profile (dict): Profile data to embed
            email (str, optional): Email address for Artist field
        """
        author = normalise_strings(profile.get("author", ""))
        copyright_holder = normalise_strings(profile.get("copyright", ""))
        license = normalise_strings(profile.get("license", ""))
        year = profile.get("year", str(datetime.now().year))
        
        # Create artist field with email if available
        if email and author:
            artist_field = f"{author} <{email}>"
        elif author:
            artist_field = author
        elif email:
            artist_field = email
        else:
            artist_field = "Unknown"
        
        # Embed standard EXIF fields
        exif_dict["0th"][piexif.ImageIFD.Artist] = artist_field.encode()
        exif_dict["0th"][piexif.ImageIFD.Copyright] = f"©{year} {copyright_holder}.".encode()
        
        # Embed XP fields with proper encoding
        exif_dict["0th"][piexif.ImageIFD.XPAuthor] = copyright_holder.encode("utf-16le")
        exif_dict["0th"][piexif.ImageIFD.XPKeywords] = license.encode("utf-16le")
    
    @staticmethod
    def extract_signature_data(exif_dict: dict) -> tuple:
        """
        Extract signature data from EXIF UserComment with format detection.
        
        Args:
            exif_dict (dict): EXIF dictionary
            
        Returns:
            tuple: (signature_str, contact_info, is_enhanced_format)
        """
        raw_user_comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment)
        if not raw_user_comment:
            return None, None, False
        
        # Load UserComment data
        user_comment_data = UserComment.load(raw_user_comment)
        
        # Try to parse as JSON (enhanced format)
        try:
            comment_json = json.loads(user_comment_data)
            if isinstance(comment_json, dict) and "signature" in comment_json:
                # Enhanced format with signature and contact info
                signature_b64 = comment_json["signature"]
                contact_info = comment_json.get("contact", {})
                
                # Decode Base64 signature
                try:
                    import base64
                    signature = base64.b64decode(signature_b64).decode("utf-8")
                    return signature, contact_info, True
                except Exception:
                    return signature_b64, contact_info, True
            else:
                return None, None, False
        except json.JSONDecodeError:
            # Legacy format - use centralized extraction
            from signature_utils import extract_signature_from_exif
            signature = extract_signature_from_exif(raw_user_comment)
            return signature, None, False
    
    @staticmethod
    def embed_enhanced_signature(exif_dict: dict, signature_b64: str, contact_data: dict) -> None:
        """
        Embed enhanced signature format with contact info into EXIF.
        
        Args:
            exif_dict (dict): EXIF dictionary to modify
            signature_b64 (str): Base64-encoded signature
            contact_data (dict): Contact information dictionary
        """
        # Combine signature with contact data
        combined_data = {
            "signature": signature_b64,
            "contact": contact_data
        }
        
        # Store as JSON in UserComment
        enhanced_comment = json.dumps(combined_data)
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = UserComment.dump(enhanced_comment)
