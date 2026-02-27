"""
crypto_fingerprint.py — Cryptographic operations for ImageIP digital signatures.

This module provides the core cryptographic functionality for ImageIP, including:

- Visual fingerprint generation combining image pixels with attribution metadata
- GPG key management with automatic generation and signing capabilities  
- Cross-platform GPG integration with automatic home directory detection
- Signature creation, verification, and key management operations

The cryptographic approach ensures that any modification to either the image content
or the embedded attribution information will result in signature verification failure,
providing strong protection against tampering.

Key Components:
    - compute_visual_hash(): Creates SHA-256 fingerprints from image + metadata
    - get_attribution_bytes(): Standardizes attribution string formatting
    - GPGManager: Comprehensive GPG operations class with automatic setup
    
Security Features:
    - Combines image pixel data with attribution metadata for comprehensive protection
    - Uses 2048-bit RSA keys with no expiration for long-term signature validity
    - Supports passphrase-free keys for improved user experience
    - Automatic trust model configuration for streamlined verification

Dependencies:
    - python-gnupg for GPG operations
    - PIL/Pillow for image processing
    - hashlib for cryptographic hashing

Author: Bernard Ennis
License: MIT
"""

import os
import tempfile
from PIL import Image
import hashlib
import os
import subprocess
import gnupg

__all__ = [
    "compute_visual_hash",
    "get_attribution_bytes",
    "GPGManager",
]

def compute_visual_hash(image_path: str, attribution: bytes, debug: bool = False) -> str:
    """
    Generate a SHA-256 fingerprint combining image pixel data with attribution metadata.
    
    This function creates a cryptographic hash that uniquely identifies both the visual
    content of an image and its associated attribution information. Any change to either
    the pixels or the attribution will result in a different hash, enabling detection
    of both visual tampering and metadata modification.
    
    Args:
        image_path (str): Path to the image file to fingerprint
        attribution (bytes): Attribution metadata as bytes (author, copyright, license info)
        debug (bool, optional): Enable debug output. Defaults to False.
        
    Returns:
        str: 64-character hexadecimal SHA-256 hash
        
    Note:
        - Images are converted to RGB or RGBA mode for consistent fingerprinting
        - Pixel data is extracted as raw bytes and combined with attribution
        - The combined data is hashed with SHA-256 for security
    """

    img = Image.open(image_path)
    mode = "RGBA" if img.mode in ("RGBA", "LA") else "RGB"
    img = img.convert(mode)
    pixel_data = img.tobytes()

    if debug:
        print("[DEBUG] Image path:", image_path)
        print("[DEBUG] Mode:", mode)
        print("[DEBUG] Attribution string:", attribution.decode("utf-8", "ignore"))
        print("[DEBUG] Attribution length:", len(attribution))
        print("[DEBUG] Pixel data sample:", pixel_data[:16])

    combined = pixel_data + attribution
    sha256 = hashlib.sha256(combined).hexdigest()

    if debug:
        print("[DEBUG] SHA-256:", sha256)

    return sha256

def get_attribution_bytes(author: str, copyright_holder: str, license: str, year: str) -> bytes:
    """
    Create standardized attribution metadata bytes for cryptographic operations.
    
    This function formats attribution information into a consistent byte string
    that can be combined with image data for fingerprinting. The format ensures
    that identical attribution information always produces identical bytes.
    
    Args:
        author (str): Name of the image author/creator
        copyright_holder (str): Name of the copyright holder (may differ from author)
        license (str): License type (e.g., "CC BY", "All rights reserved")
        year (str): Year of creation or copyright
        
    Returns:
        bytes: UTF-8 encoded attribution string in format "author ©year copyright_holder. license"
        
    Example:
        >>> get_attribution_bytes("John Doe", "Acme Corp", "CC BY", "2024")
        b'John Doe ©2024 Acme Corp. CC BY'
    """
    return f"{author} ©{year} {copyright_holder}. {license}".encode("utf-8")

class GPGManager:
    """
    A class for generating, exporting, signing, and verifying data with GPG.
    """

    def __init__(self):
        try:
            self.gpg_home = self._detect_gpg_home()
            print(f"[DEBUG] Using GPG home: {self.gpg_home}")
            self.gpg = gnupg.GPG(gnupghome=self.gpg_home)
            
            # Configure GPG for non-interactive operation
            self.gpg.options = [
                "--pinentry-mode", "loopback",
                "--batch",
                "--no-tty", 
                "--yes",  # Automatically answer yes to questions
                "--quiet",
                "--trust-model", "always"  # Trust all keys automatically
            ]
            
            # Test GPG functionality
            version = self.gpg.version
            print(f"[DEBUG] GPG initialized successfully. Version: {version}")
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize GPG: {e}")
            raise RuntimeError(f"GPG initialization failed: {e}")

    def _detect_gpg_home(self) -> str:
        """
        Detects the system GPG home directory.

        Returns:
            str: Path to GPG home.

        Raises:
            RuntimeError: If the home directory cannot be determined.
        """
        import platform
        
        # Try environment variable first
        gpg_home = os.environ.get('GNUPGHOME')
        if gpg_home and os.path.exists(gpg_home):
            print(f"[DEBUG] Using GNUPGHOME from environment: {gpg_home}")
            return gpg_home
        
        # Try platform-specific defaults
        system = platform.system()
        if system == "Windows":
            # Windows default locations
            possible_paths = [
                os.path.expanduser("~/.gnupg"),
                os.path.join(os.environ.get('APPDATA', ''), 'gnupg'),
                os.path.join(os.environ.get('USERPROFILE', ''), '.gnupg')
            ]
        else:
            # Unix-like systems
            possible_paths = [os.path.expanduser("~/.gnupg")]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"[DEBUG] Found existing GPG home: {path}")
                return path
        
        # Try to get from GPG command
        try:
            result = subprocess.run(["gpg", "--version"], capture_output=True, text=True, timeout=10)
            for line in result.stdout.splitlines():
                if line.startswith("Home:"):
                    gpg_home = line.split(":", 1)[1].strip()
                    print(f"[DEBUG] GPG home from command: {gpg_home}")
                    return gpg_home
        except Exception as e:
            print(f"[DEBUG] Could not get GPG home from command: {e}")
        
        # Create default if none exists
        default_home = os.path.expanduser("~/.gnupg")
        print(f"[DEBUG] Creating default GPG home: {default_home}")
        os.makedirs(default_home, mode=0o700, exist_ok=True)
        return default_home

    def key_exists(self, identifier: str) -> bool:
        """
        Checks whether a key with the given identifier (such as an email or fingerprint) exists in the keyring.

        Args:
            identifier (str): Email or fingerprint to check.
        
        Returns:
            bool: True if a key matching the identifier exists, False otherwise.
        """
        return any(identifier in uid for key in self.gpg.list_keys() for uid in key.get("uids", []))

    def generate_key(self, name_email: str, passphrase: str = "") -> str:
        """
        Generates a GPG key for the given email and returns its fingerprint.

        Args:
            name_email (str): Email address for which the key will be generated.
            passphrase (str, optional): Passphrase for the key (default is empty).

        Returns:
            str: The fingerprint of the generated key.
        
        Raises:
            ValueError: If key generation fails.
        """
        print(f"[DEBUG] Starting key generation for: {name_email}")
        
        # Extract name from email
        name = name_email.split("@")[0].replace(".", " ").title()
        print(f"[DEBUG] Extracted name: {name}")
        
        # Check if key already exists
        existing_keys = self.gpg.list_keys(secret=True)
        for key in existing_keys:
            for uid in key.get('uids', []):
                if name_email in uid:
                    print(f"[DEBUG] Key already exists for {name_email}: {key['fingerprint']}")
                    return key['fingerprint']
        
        # Try the most reliable method first - direct subprocess with proper GPG options
        try:
            print("[DEBUG] Trying direct subprocess method...")
            
            # Create a temporary key generation script with explicit batch mode settings
            import tempfile
            
            # Create key generation parameters file
            key_params = f"""Key-Type: RSA
Key-Length: 2048
Subkey-Type: RSA  
Subkey-Length: 2048
Name-Real: {name}
Name-Email: {name_email}
Expire-Date: 0
%no-ask-passphrase
%no-protection
%commit
"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(key_params)
                params_file = f.name
            
            print(f"[DEBUG] Created key parameters file: {params_file}")
            print(f"[DEBUG] Parameters:\n{key_params}")
            
            # Set up environment for batch operation
            env = os.environ.copy()
            env['GPG_TTY'] = ''  # Disable TTY
            
            # Run GPG with explicit batch mode and no-tty options
            cmd = [
                "gpg", 
                "--batch",
                "--no-tty", 
                "--yes",
                "--quiet",
                "--generate-key",
                params_file
            ]
            
            print(f"[DEBUG] Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=120,
                env=env
            )
            
            print(f"[DEBUG] GPG command exit code: {result.returncode}")
            print(f"[DEBUG] GPG stdout: {result.stdout}")
            print(f"[DEBUG] GPG stderr: {result.stderr}")
            
            # Clean up params file
            try:
                os.unlink(params_file)
            except:
                pass
            
            if result.returncode == 0:
                # Key generation successful, find the new key
                print("[DEBUG] Key generation completed, searching for new key...")
                
                # Refresh the GPG instance and search for the key
                self.gpg = gnupg.GPG(gnupghome=self.gpg_home)
                keys = self.gpg.list_keys(secret=True)
                
                for key in keys:
                    for uid in key.get('uids', []):
                        if name_email in uid:
                            fingerprint = key['fingerprint']
                            print(f"[DEBUG] Found generated key fingerprint: {fingerprint}")
                            return fingerprint
                
                raise ValueError("Key generated but could not find fingerprint in keyring")
            else:
                print(f"[DEBUG] Direct subprocess failed with code {result.returncode}")
                
        except Exception as e:
            print(f"[DEBUG] Direct subprocess method failed: {e}")
        
        # Fallback to python-gnupg with enhanced settings
        try:
            print("[DEBUG] Trying python-gnupg fallback method...")
            
            # Create a new GPG instance with batch mode settings
            gpg_options = [
                '--batch',
                '--no-tty', 
                '--yes',
                '--quiet',
                '--trust-model', 'always'
            ]
            
            # Create temporary GPG instance with batch settings
            temp_gpg = gnupg.GPG(
                gnupghome=self.gpg_home,
                options=gpg_options
            )
            
            # Generate key input with all necessary directives
            input_data = temp_gpg.gen_key_input(
                name_real=name,
                name_email=name_email,
                passphrase="",  # Always use empty passphrase
                key_type="RSA",
                key_length=2048,
                expire_date=0
            )
            
            # Add additional directives for unattended generation
            input_data += "%no-ask-passphrase\n"
            input_data += "%no-protection\n"
            
            print(f"[DEBUG] Using input data:\n{input_data}")
            
            # Generate the key
            key = temp_gpg.gen_key(input_data)
            
            print(f"[DEBUG] Key generation result: {key}")
            print(f"[DEBUG] Key status: {key.status}")
            print(f"[DEBUG] Key stderr: {key.stderr}")
            print(f"[DEBUG] Key fingerprint: {key.fingerprint}")
            
            if key and key.fingerprint:
                # Refresh main GPG instance
                self.gpg = gnupg.GPG(gnupghome=self.gpg_home)
                return key.fingerprint
            else:
                error_msg = f"Python-gnupg method failed. Status: {key.status if key else 'None'}"
                if key and key.stderr:
                    error_msg += f", stderr: {key.stderr}"
                raise ValueError(error_msg)
                
        except Exception as e:
            print(f"[DEBUG] Python-gnupg fallback failed: {e}")
            raise ValueError(f"All key generation methods failed. Last error: {e}")

    def export_public_key(self, fingerprint: str, output_path: str) -> None:
        """
        Exports the public key associated with the fingerprint to a file.

        Args:
            fingerprint (str): The fingerprint of the key.
            output_path (str): Path of the output file to save the key.
        
        Raises:
            ValueError: If the exported key is malformed.
        """
        ascii_key = self.gpg.export_keys(fingerprint)
        if "BEGIN PGP PUBLIC KEY BLOCK" not in ascii_key:
            raise ValueError("Malformed public key")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ascii_key)

    def ensure_key_in_keyring(self, fingerprint: str) -> None:
        """
        Ensures that the public key is imported in the keyring.

        Args:
            fingerprint (str): The fingerprint of the key.
        """
        if not any(k["fingerprint"] == fingerprint for k in self.gpg.list_keys()):
            ascii_key = self.gpg.export_keys(fingerprint)
            self.gpg.import_keys(ascii_key)

    def generate_and_export(self, name_email: str, output_dir: str = ".", filename: str = "exported_key.key") -> str:
        """
        Generates a key, exports the public key, and ensures it is present in the keyring.

        Args:
            name_email (str): Email address for the new key.
            output_dir (str): Directory to store the exported key.
            filename (str): Filename for the exported key (default: 'exported_key.key').

        Returns:
            str: The path to the exported public key file.
        """
        fingerprint = self.generate_key(name_email)
        key_path = os.path.join(output_dir, filename)
        self.export_public_key(fingerprint, key_path)
        self.ensure_key_in_keyring(fingerprint)
        return key_path

    def sign_data(self, data: str, keyid: str = None, detach: bool = True, passphrase: str = "") -> str:
        """
        Signs the given data (message) using the specified key and returns an ASCII-armored signature.

        Args:
            data (str): The message/data to sign.
            keyid (str, optional): Key identifier (fingerprint or short keyid) to sign with.
            detach (bool, optional): Whether to create a detached signature (default True).
            passphrase (str, optional): The passphrase for the signing key (default empty).

        Returns:
            str: The ASCII-armored signature.

        Raises:
            ValueError: If signing fails.
        """
        print(f"[DEBUG] Signing with keyid: {keyid}")
        print(f"[DEBUG] Signing without passphrase (new key)")
        
        # Sign with new passphrase-less key
        result = self.gpg.sign(message=data, keyid=keyid, detach=detach)
        
        # Debug output:
        print("[DEBUG] Raw signing result repr:", repr(result))
        print("[DEBUG] Result data:", result.data)
        print("[DEBUG] Result stderr:", result.stderr)
        
        # Use the data attribute and decode it from bytes to a string
        signature = result.data.decode("utf-8").strip() if result.data else ""
        
        if not signature:
            raise ValueError(f"Signing failed: No result returned. stderr: {result.stderr}")
        
        # Check for actual errors in stderr (ignore informational messages)
        if result.stderr:
            error_indicators = ["error", "failed", "bad passphrase", "invalid"]
            stderr_lower = result.stderr.lower()
            if any(indicator in stderr_lower for indicator in error_indicators):
                # Only raise error if stderr contains actual error indicators
                if not any(success in stderr_lower for success in ["sig_created", "begin_signing"]):
                    raise ValueError(f"Signing error: {result.stderr}")
        
        return signature

    def verify_data(self, data: str, signature_file: str) -> bool:
        """
        Verifies the given data against its detached signature file.
        
        Args:
            data (str): The data that was signed (SHA-256 hash)
            signature_file (str): Path to the temporary signature file
            
        Returns:
            bool: True if verification is valid
        """
        # Ensure the data is bytes
        data_bytes = data if isinstance(data, bytes) else data.encode("utf-8")
        
        verification = self.gpg.verify_data(signature_file, data_bytes)

        # Debug output to see GPG's response
        print("[DEBUG] verification.valid:", verification.valid)
        print("[DEBUG] verification.status:", verification.status)
        print("[DEBUG] verification.fingerprint:", verification.fingerprint)

        return verification and verification.valid

# Create a single instance for use across the project:
gpg_manager = GPGManager()