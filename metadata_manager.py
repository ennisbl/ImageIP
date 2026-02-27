"""
metadata_manager.py — Enhanced metadata management for ImageIP.

This module provides advanced metadata embedding and extraction capabilities,
including email contact information, structured profile data, and standard
EXIF/IPTC fields for comprehensive image attribution.

Key Features:
    - Email address embedding in multiple metadata fields
    - Structured profile data storage in UserComment
    - Standard EXIF Artist and Copyright field handling
    - JSON-based contact information storage
    - Backwards compatibility with existing signatures

The module embeds email and contact information in multiple locations:
    1. EXIF Artist field (Name <email> format)
    2. JSON structure in UserComment (alongside signature)
    3. Standard copyright fields for maximum compatibility

Author: Bernard Ennis
License: MIT
"""

import json
import piexif
from PIL import Image
from datetime import datetime
from typing import Dict, Optional, Tuple
import re

def embed_profile_metadata(image_path: str, profile: Dict, preserve_signature: bool = True) -> bool:
    """
    Embed comprehensive profile metadata into image EXIF data.
    
    Args:
        image_path: Path to the image file
        profile: Profile dictionary containing metadata
        preserve_signature: Whether to preserve existing signature data
        
    Returns:
        True if metadata was successfully embedded, False otherwise
    """
    try:
        # Open image and get existing EXIF
        image = Image.open(image_path)
        
        try:
            exif_dict = piexif.load(image_path)
        except Exception:
            # Create new EXIF structure if none exists
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        
        # Extract profile information
        author = profile.get('author', '')
        copyright_holder = profile.get('copyright', '')
        email = profile.get('email', '') or profile.get('gpg_key', '')  # Use email field or fall back to GPG key
        license_info = profile.get('license', '')
        
        # 1. Embed email in Artist field (Name <email> format)
        if author and email:
            artist_field = f"{author} <{email}>"
        elif author:
            artist_field = author
        elif email:
            artist_field = email
        else:
            artist_field = "Unknown"
            
        exif_dict["0th"][piexif.ImageIFD.Artist] = artist_field.encode('utf-8')
        
        # 2. Update copyright information
        year = datetime.now().year
        if copyright_holder:
            copyright_field = f"©{year} {copyright_holder}."
        else:
            copyright_field = f"©{year} {author}." if author else f"©{year}"
        
        exif_dict["0th"][piexif.ImageIFD.Copyright] = copyright_field.encode('utf-8')
        
        # 3. Add license information to keywords field
        if license_info:
            exif_dict["0th"][piexif.ImageIFD.XPKeywords] = license_info.encode("utf-16le")
        
        # 4. Add additional contact fields if available
        if copyright_holder:
            exif_dict["0th"][piexif.ImageIFD.XPAuthor] = copyright_holder.encode("utf-16le")
        
        # 5. Save EXIF data back to image
        exif_bytes = piexif.dump(exif_dict)
        image.save(image_path, exif=exif_bytes, quality=95)
        
        return True
        
    except Exception as e:
        print(f"Error embedding profile metadata: {e}")
        return False

def extract_profile_metadata(image_path: str) -> Dict:
    """
    Extract profile and contact information from image metadata.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary containing extracted profile information
    """
    profile_data = {
        "author": None,
        "email": None,
        "copyright": None,
        "license": None,
        "has_signature": False
    }
    
    try:
        # Load EXIF data
        exif_dict = piexif.load(image_path)
        
        # Extract Artist information (may contain email)
        if piexif.ImageIFD.Artist in exif_dict["0th"]:
            artist = exif_dict["0th"][piexif.ImageIFD.Artist].decode('utf-8')
            profile_data["author"] = artist
            
            # Try to extract email from "Name <email>" format
            email_match = re.search(r'<([^>]+)>', artist)
            if email_match:
                profile_data["email"] = email_match.group(1)
                # Clean author name (remove email part)
                profile_data["author"] = re.sub(r'\s*<[^>]+>', '', artist).strip()
        
        # Extract Copyright information
        if piexif.ImageIFD.Copyright in exif_dict["0th"]:
            copyright_info = exif_dict["0th"][piexif.ImageIFD.Copyright].decode('utf-8')
            profile_data["copyright"] = copyright_info
        
        # Extract License from keywords
        if piexif.ImageIFD.XPKeywords in exif_dict["0th"]:
            try:
                xp_keywords_data = exif_dict["0th"][piexif.ImageIFD.XPKeywords]
                if isinstance(xp_keywords_data, tuple):
                    # Convert tuple of bytes to bytes, then decode
                    license_info = bytes(xp_keywords_data).decode('utf-16le').strip()
                elif isinstance(xp_keywords_data, bytes):
                    license_info = xp_keywords_data.decode('utf-16le').strip()
                else:
                    license_info = str(xp_keywords_data)
                profile_data["license"] = license_info
            except Exception as e:
                print(f"Warning: Could not decode XPKeywords: {e}")
        
        # Extract Copyright Author from XPAuthor
        if piexif.ImageIFD.XPAuthor in exif_dict["0th"]:
            try:
                xp_author_data = exif_dict["0th"][piexif.ImageIFD.XPAuthor]
                if isinstance(xp_author_data, tuple):
                    # Convert tuple of bytes to bytes, then decode
                    xp_author = bytes(xp_author_data).decode('utf-16le').strip()
                elif isinstance(xp_author_data, bytes):
                    xp_author = xp_author_data.decode('utf-16le').strip()
                else:
                    xp_author = str(xp_author_data)
                # Only override if we don't already have copyright info
                if not profile_data.get("copyright"):
                    profile_data["copyright"] = xp_author
            except Exception as e:
                print(f"Warning: Could not decode XPAuthor: {e}")
        
        # Check for contact data in UserComment
        if piexif.ExifIFD.UserComment in exif_dict["Exif"]:
            try:
                from piexif.helper import UserComment
                user_comment = UserComment.load(exif_dict["Exif"][piexif.ExifIFD.UserComment])
                
                # Try to parse as JSON
                try:
                    comment_data = json.loads(user_comment)
                    
                    # Check if it's structured data with contact info
                    if isinstance(comment_data, dict):
                        if "contact" in comment_data:
                            # New format with signature + contact
                            contact = comment_data["contact"]
                            profile_data.update({
                                "email": contact.get("email"),
                                "author": contact.get("author"),
                                "copyright": contact.get("copyright"),
                                "license": contact.get("license")
                            })
                            profile_data["has_signature"] = "signature" in comment_data
                        elif "email" in comment_data:
                            # Direct contact data format
                            profile_data.update({
                                "email": comment_data.get("email"),
                                "author": comment_data.get("author"),
                                "copyright": comment_data.get("copyright"),
                                "license": comment_data.get("license")
                            })
                except json.JSONDecodeError:
                    # UserComment contains non-JSON data (likely just signature)
                    profile_data["has_signature"] = True
                    
            except Exception as e:
                print(f"Warning: Could not parse UserComment: {e}")
        
        # Remove None values
        profile_data = {k: v for k, v in profile_data.items() if v is not None}
        
    except Exception as e:
        print(f"Error extracting profile metadata: {e}")
    
    return profile_data

def extract_signature_from_usercomment(image_path: str) -> Optional[str]:
    """
    Extract just the signature data from UserComment field.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 signature string if found, None otherwise
    """
    try:
        exif_dict = piexif.load(image_path)
        
        if piexif.ExifIFD.UserComment in exif_dict["Exif"]:
            from piexif.helper import UserComment
            user_comment = UserComment.load(exif_dict["Exif"][piexif.ExifIFD.UserComment])
            
            # Try to parse as JSON first
            try:
                comment_data = json.loads(user_comment)
                if isinstance(comment_data, dict) and "signature" in comment_data:
                    return comment_data["signature"]
            except json.JSONDecodeError:
                # Assume it's a plain signature if not JSON
                if user_comment and len(user_comment) > 50:  # Reasonable signature length
                    return user_comment
                    
    except Exception as e:
        print(f"Error extracting signature: {e}")
    
    return None

def format_contact_info(profile: Dict) -> str:
    """
    Format profile information for display.
    
    Args:
        profile: Profile dictionary
        
    Returns:
        Formatted contact information string
    """
    lines = []
    
    if profile.get('author'):
        lines.append(f"Author: {profile['author']}")
    
    if profile.get('email'):
        lines.append(f"Email: {profile['email']}")
    
    if profile.get('copyright'):
        lines.append(f"Copyright: {profile['copyright']}")
    
    if profile.get('license'):
        lines.append(f"License: {profile['license']}")
    
    return "\n".join(lines) if lines else "No contact information available"

def verify_metadata_integrity(image_path: str) -> Tuple[bool, str]:
    """
    Verify that embedded metadata is intact and readable.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple of (is_valid, description)
    """
    try:
        profile = extract_profile_metadata(image_path)
        
        if not profile or len(profile) <= 1:  # Only has_signature field
            return False, "No embedded metadata found"
        
        required_fields = ['author', 'email']
        missing_fields = [field for field in required_fields if not profile.get(field)]
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        return True, "Metadata is complete and readable"
        
    except Exception as e:
        return False, f"Error verifying metadata: {e}"

if __name__ == "__main__":
    # Test the metadata functions
    test_profile = {
        "author": "John Doe",
        "gpg_key": "john.doe@example.com",
        "copyright": "John Doe Photography",
        "license": "CC BY 4.0"
    }
    
    print("Test profile:")
    print(format_contact_info(test_profile))
