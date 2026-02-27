"""
verification_service.py — Centralized signature verification service

This service consolidates all signature verification logic to eliminate duplication
across the application and provide a consistent verification interface.

Key Features:
    - Unified signature extraction and format detection
    - Consistent profile handling and reconstruction
    - Centralized GPG verification workflow
    - Base64 encoding/decoding standardization

Author: Bernard Ennis
License: MIT
"""

import os
import json
from signature_utils import write_signature_to_temp_file, compute_image_fingerprint
from exif_service import EXIFService
from crypto_fingerprint import gpg_manager


class VerificationService:
    """Centralized service for signature verification operations."""
    
    @staticmethod
    def verify_image_signature(image_path: str, profile: dict = None, debug: bool = False, return_details: bool = False):
        """
        Verify the signature embedded in an image's EXIF metadata.
        
        This is the main verification method that handles both profile-based verification
        (when profile is provided) and EXIF-extracted verification (when profile is None).
        
        Args:
            image_path (str): Path to the image file
            profile (dict, optional): Profile data. If None, extracts from EXIF
            debug (bool, optional): Enable debug output
            return_details (bool, optional): If True, returns detailed dict instead of bool
            
        Returns:
            bool or dict: True if signature is valid, False otherwise. 
                         If return_details=True, returns detailed verification information.
        """
        try:
            # Load EXIF data
            exif_dict = EXIFService.load_exif_safely(image_path)
            
            # Extract signature data
            signature_str, contact_info, is_enhanced_format = EXIFService.extract_signature_data(exif_dict)
            
            if not signature_str:
                if debug:
                    print("[DEBUG] No signature found in image EXIF metadata.")
                if return_details:
                    return {
                        "is_valid": False,
                        "embedded_profile": None,
                        "provided_profile": profile,
                        "profile_match": False,
                        "contact_info": None,
                        "is_enhanced_format": False,
                        "error_message": "No signature found in image EXIF metadata"
                    }
                return False
            
            # Extract the original profile from EXIF
            embedded_profile = EXIFService.extract_profile_from_exif(image_path)
            
            # Use provided profile or extracted profile
            verification_profile = profile if profile is not None else embedded_profile
            
            # Check if profiles match (only relevant when profile is provided)
            profile_match = True
            gpg_key_match = True
            if profile is not None:
                profile_match = (
                    embedded_profile.get('author') == profile.get('author') and
                    embedded_profile.get('copyright') == profile.get('copyright') and
                    embedded_profile.get('license') == profile.get('license')
                )
                
                # Check if GPG keys match
                embedded_email = contact_info.get('email') if contact_info else None
                profile_email = profile.get('email') or profile.get('gpg_key')
                gpg_key_match = (embedded_email == profile_email) if embedded_email and profile_email else True
            
            if debug:
                print(f"[DEBUG] Extracted profile from EXIF: {embedded_profile}")
                print(f"[DEBUG] Using profile: {verification_profile}")
                print(f"[DEBUG] Profile match: {profile_match}")
                print(f"[DEBUG] GPG key match: {gpg_key_match}")
                if contact_info:
                    print(f"[DEBUG] Embedded GPG email: {contact_info.get('email', 'N/A')}")
                    print(f"[DEBUG] Profile GPG email: {profile.get('email') or profile.get('gpg_key', 'N/A') if profile else 'N/A'}")
                print(f"[DEBUG] Found {'enhanced' if is_enhanced_format else 'legacy'} signature format")
                if contact_info:
                    print(f"[DEBUG] Contact info: {contact_info.get('email', 'N/A')}")
                print(f"[DEBUG] Final signature for verification: {repr(signature_str[:100] + '...' if len(signature_str) > 100 else signature_str)}")
            
            # Compute image fingerprint with verification profile
            sha256 = compute_image_fingerprint(image_path, verification_profile, debug=debug)
            if debug:
                print(f"[DEBUG] Computed SHA-256 hash: {sha256}")
            
            # Verify signature using GPG
            verification_result = VerificationService._verify_gpg_signature(signature_str, sha256, debug)
            
            if return_details:
                # Determine error message
                error_message = None
                if not verification_result:
                    if profile is not None and not gpg_key_match:
                        embedded_email = contact_info.get('email') if contact_info else 'Unknown'
                        profile_email = profile.get('email') or profile.get('gpg_key', 'Unknown')
                        error_message = f"GPG key mismatch: Image was signed with '{embedded_email}' but verifying with '{profile_email}'. Use the correct GPG key or profile."
                    elif profile is not None and not profile_match:
                        error_message = f"Profile mismatch: Image was signed with copyright holder '{embedded_profile.get('copyright')}', but verifying with '{profile.get('copyright')}'"
                    else:
                        error_message = "Signature verification failed - image may have been tampered with"
                
                return {
                    "is_valid": verification_result,
                    "embedded_profile": embedded_profile,
                    "provided_profile": profile,
                    "profile_match": profile_match,
                    "gpg_key_match": gpg_key_match,
                    "contact_info": contact_info,
                    "is_enhanced_format": is_enhanced_format,
                    "error_message": error_message
                }
            
            return verification_result
            
        except Exception as e:
            if debug:
                print(f"[DEBUG] Verification failed with error: {e}")
            if return_details:
                return {
                    "is_valid": False,
                    "embedded_profile": None,
                    "provided_profile": profile,
                    "profile_match": False,
                    "gpg_key_match": False,
                    "contact_info": None,
                    "is_enhanced_format": False,
                    "error_message": f"Verification error: {str(e)}"
                }
            return False
    
    @staticmethod
    def _verify_gpg_signature(signature_str: str, data_hash: str, debug: bool = False) -> bool:
        """
        Verify GPG signature against data hash.
        
        Args:
            signature_str (str): GPG signature string
            data_hash (str): SHA-256 hash of the data
            debug (bool, optional): Enable debug output
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            # Write signature to temporary file
            tmp_sig_filename = write_signature_to_temp_file(signature_str)
            
            try:
                # Verify using GPG manager
                verification_result = gpg_manager.verify_data(data_hash, tmp_sig_filename)
                
                if debug:
                    print(f"[DEBUG] verification.valid: {verification_result.valid if hasattr(verification_result, 'valid') else bool(verification_result)}")
                    if hasattr(verification_result, 'status'):
                        print(f"[DEBUG] verification.status: {verification_result.status}")
                    if hasattr(verification_result, 'fingerprint'):
                        print(f"[DEBUG] verification.fingerprint: {verification_result.fingerprint}")
                
                # Handle different return types from GPG manager
                if hasattr(verification_result, 'valid'):
                    return verification_result.valid
                else:
                    return bool(verification_result)
                    
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_sig_filename):
                    os.unlink(tmp_sig_filename)
                    
        except Exception as e:
            if debug:
                print(f"[DEBUG] GPG verification failed: {e}")
            return False
    
    @staticmethod
    def verify_with_profile(image_path: str, profile: dict, debug: bool = False) -> bool:
        """
        Verify signature using a specific profile (GUI verification mode).
        
        Args:
            image_path (str): Path to the image file
            profile (dict): Profile data to use for verification
            debug (bool, optional): Enable debug output
            
        Returns:
            bool: True if signature is valid, False otherwise
            
        Raises:
            ValueError: If signature verification fails
        """
        result = VerificationService.verify_image_signature(image_path, profile, debug)
        
        if not result:
            raise ValueError("Signature verification failed.")
            
        return result
    
    @staticmethod
    def verify_with_profile_detailed(image_path: str, profile: dict, debug: bool = False) -> dict:
        """
        Verify signature using a specific profile and return detailed information.
        
        Args:
            image_path (str): Path to the image file
            profile (dict): Profile data to use for verification
            debug (bool, optional): Enable debug output
            
        Returns:
            dict: Detailed verification results including:
                - is_valid (bool): True if signature is valid
                - embedded_profile (dict): Profile data extracted from EXIF
                - provided_profile (dict): Profile data provided for verification
                - profile_match (bool): True if profiles match
                - error_message (str): Error description if verification fails
        """
        return VerificationService.verify_image_signature(
            image_path, profile, debug=debug, return_details=True
        )
    
    @staticmethod
    def verify_with_exif_extraction(image_path: str, debug: bool = False) -> bool:
        """
        Verify signature by extracting profile data from EXIF (View Signature mode).
        
        Args:
            image_path (str): Path to the image file
            debug (bool, optional): Enable debug output
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        return VerificationService.verify_image_signature(image_path, None, debug)
    
    @staticmethod
    def get_signature_info(image_path: str) -> dict:
        """
        Extract signature and contact information from image.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Dictionary with signature, contact_info, and format information
        """
        try:
            exif_dict = EXIFService.load_exif_safely(image_path)
            signature_str, contact_info, is_enhanced_format = EXIFService.extract_signature_data(exif_dict)
            
            return {
                "signature": signature_str,
                "contact_info": contact_info,
                "is_enhanced_format": is_enhanced_format,
                "has_signature": bool(signature_str)
            }
        except Exception:
            return {
                "signature": None,
                "contact_info": None,
                "is_enhanced_format": False,
                "has_signature": False
            }
