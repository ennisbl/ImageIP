# signature_verifier.py
import os
from signature_utils import extract_signature_from_exif, write_signature_to_temp_file, compute_image_fingerprint

def verify_image_signature(image_path: str, profile: dict, debug: bool=False) -> bool:
    """
    Verifies the signature embedded in the image’s EXIF metadata using a centralized extraction routine.
    """
    import piexif
    from crypto_fingerprint import gpg_manager

    try:
        exif_dict = piexif.load(image_path)
        raw_user_comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment)
        if not raw_user_comment:
            raise ValueError("No signature found in image EXIF metadata.")
        # Use the common extraction method
        signature_str = extract_signature_from_exif(raw_user_comment)
    except Exception as e:
        raise ValueError("Failed to load signature from image EXIF: " + str(e))
    
    if debug:
        print("[DEBUG] Final signature for verification:", repr(signature_str))
    
    # Recompute the image's SHA-256 hash with attribution
    sha256 = compute_image_fingerprint(image_path, profile, debug=debug)
    if debug:
        print("[DEBUG] Computed SHA-256 hash:", sha256)
    
    # Write signature to temp file via centralized function:
    tmp_sig_filename = write_signature_to_temp_file(signature_str)
    verification_result = gpg_manager.verify_data(sha256, tmp_sig_filename)
    os.unlink(tmp_sig_filename)
    
    if not verification_result:
        raise ValueError("Signature verification failed.")
    
    return True
