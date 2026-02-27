"""
gui.py — User interface for ImageIP Digital Rights Management Tool.

This module provides the main graphical user interface for ImageIP, which enables
photographers and content creators to:

- Create and manage signing profiles
- Digitally sign images with cryptographic signatures
- Embed copyright and licensing metadata into i                                             messagebox.showwarning("PDF Not Found", "PDF file not found. Please generate PDF first.")
                        
                        # Automatically generate PDF report with same filename as image
                        if PDF_AVAILABLE:                       messagebox.showwarning("PDF Not Found", "PDF file not found. Please generate PDF first.")
                        
                        # Automatically generate PDF report with same filename as image            # Automatically generate PDF report with same filename as image
                        if PDF_AVAILABLE:
                            try:
                                pdf_file_path = generate_verification_pdf()
                                if pdf_file_path:
                                    # Add Open PDF button only if PDF was successfully created
                                    ttk.Button(button_frame_bottom, text="📖 Open PDF", command=open_pdf_report).pack(side="left", padx=(0, 10))
                            except Exception as e:
                                print(f"Failed to auto-generate PDF: {e}")               messagebox.showwarning("PDF Not Found", "PDF file not found. Please generate PDF first.")
                        
                        # Automatically generate PDF report with same filename as image
                        if PDF_AVAILABLE:                 
                        # Automatically generate PDF report with same filename as imagefiles
- Verify the authenticity and integrity of signed images
- Browse and view embedded signatures

The GUI provides an intuitive interface for all core ImageIP functionality,
including automatic GPG key generation, batch folder processing, and
signature verification.

Key Components:
    - Profile management (create, edit, delete, select)
    - Folder-based image signing workflow
    - Signature viewing and verification tools
    - Cross-platform file handling

Dependencies:
    - tkinter (GUI framework)
    - profile_manager (profile creation and management)
    - signing_engine (core signing functionality)
    - signature_viewer (signature display)
    - verification_service (signature validation)

Author: Bernard Ennis
License: MIT
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from datetime import datetime

# Try to import PDF generation
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    print("Warning: PDF generation not available. Install reportlab: pip install reportlab")
    PDF_AVAILABLE = False

# Correct local module imports:
from profile_manager import (
    launch_profile_browser,
    prompt_for_profile,
    save_profiles,
    load_profiles,
    save_last_used_profile,
    load_last_used_profile
)
from signing_engine import sign_images_in_folder
from signature_viewer import view_embedded_signature
from verification_service import VerificationService
from utils import extract_creation_datetime
from metadata_manager import extract_profile_metadata, format_contact_info

# Try to import image comparison modules
try:
    from image_comparison import ImageComparator, CopyrightDatabase
    COMPARISON_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Image comparison features not available: {e}")
    COMPARISON_AVAILABLE = False

def create_pdf_report(content: str, base_filename: str, report_type: str = "report") -> str:
    """
    Create a PDF report from text content.
    
    Args:
        content: The text content to include in the PDF
        base_filename: Base filename (without extension) for the PDF
        report_type: Type of report (e.g., "verification", "comparison")
        
    Returns:
        Path to the created PDF file, or None if creation failed
    """
    if not PDF_AVAILABLE:
        return None
        
    pdf_path = f"{base_filename}_{report_type}_report.pdf"
    
    try:
        # Create PDF document
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add ImageIP logo to header
        try:
            # Try to find the logo file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(script_dir, "assets", "ImageIP_logo.png")
            
            if os.path.exists(logo_path):
                # Add logo with reasonable size (1.5 inches wide, maintaining aspect ratio)
                logo = Image(logo_path, width=1.5*inch, height=1.5*inch)
                story.append(logo)
                story.append(Spacer(1, 0.2*inch))
        except Exception as e:
            print(f"Warning: Could not add logo to PDF: {e}")
        
        # Determine title based on report type
        if "verification" in report_type.lower():
            title = "SIGNATURE VERIFICATION RESULTS"
        elif "comparison" in report_type.lower():
            title = "IMAGE COMPARISON RESULTS"
        else:
            title = "REPORT"
            
        # Add title
        title_para = Paragraph(title, styles['Title'])
        story.append(title_para)
        story.append(Spacer(1, 0.2*inch))
        
        # Process content lines
        content_lines = content.split('\n')
        for line in content_lines:
            if line.strip():
                if line.startswith('='):
                    continue  # Skip separator lines
                
                # Replace Unicode symbols with text equivalents for PDF
                pdf_line = line.replace('✅', '[VERIFIED]')
                pdf_line = pdf_line.replace('❌', '[FAILED]')
                pdf_line = pdf_line.replace('🎯', '[MATCH]')
                pdf_line = pdf_line.replace('🔍', '[SEARCH]')
                pdf_line = pdf_line.replace('📂', '[FOLDER]')
                pdf_line = pdf_line.replace('💾', '[SAVE]')
                pdf_line = pdf_line.replace('•', '*')
                
                # Style based on content
                if line.startswith('✅') or 'AUTHENTIC' in line or 'MATCH' in line:
                    para = Paragraph(f"<b>{pdf_line}</b>", styles['Heading2'])
                elif line.endswith(':') and not line.startswith('*'):
                    para = Paragraph(f"<b>{pdf_line}</b>", styles['Heading3'])
                else:
                    para = Paragraph(pdf_line, styles['Normal'])
                story.append(para)
                story.append(Spacer(1, 0.1*inch))
        
        # Add generation timestamp
        story.append(Spacer(1, 0.3*inch))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer = Paragraph(f"<i>Report generated on {timestamp} by ImageIP</i>", styles['Normal'])
        story.append(footer)
        
        # Build PDF
        doc.build(story)
        return pdf_path
        
    except Exception as e:
        print(f"Failed to generate PDF: {e}")
        return None

def get_version():
    """Get version from setup.py without triggering setuptools."""
    import os
    import re
    setup_path = os.path.join(os.path.dirname(__file__), 'setup.py')
    with open(setup_path, 'r') as f:
        content = f.read()
    
    # Find VERSION = "x.x.x" pattern
    version_match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
    if version_match:
        return version_match.group(1)
    return "1.1.0"  # fallback

def launch_gui():
    """Start the ImageIP main window."""
    root = tk.Tk()
    root.title(f"ImageIP — Digital Rights & Signature Assistant v{get_version()}")
    root.geometry("450x450")
    root.resizable(True, True)

    ttk.Label(root, text="Welcome to ImageIP", font=("Segoe UI", 16)).pack(pady=(15, 5))

    # Active profile tracker
    _selected_profile = {}
    active_profile_text = tk.StringVar(value="No profile selected")
    ttk.Label(root, textvariable=active_profile_text, font=("Segoe UI", 9, "italic"), foreground="#444").pack()

    profiles = load_profiles()
    last_name = load_last_used_profile()
    if last_name and last_name in profiles:
        _selected_profile = profiles[last_name]
        active_profile_text.set(f"Active Profile: {last_name}")

    # Initialize copyright comparison system
    copyright_db = None
    image_comparator = None
    if COMPARISON_AVAILABLE:
        try:
            copyright_db = CopyrightDatabase()
            image_comparator = ImageComparator()
            print("Copyright verification system initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize copyright verification: {e}")

    # Global variable to store selected suspected copy
    _selected_suspected_copy = None
    
    # Status text for copyright protection section
    status_text = tk.StringVar(value="No suspected copy selected")

    button_frame = ttk.Frame(root)
    button_frame.pack()

    open_folder_var = tk.BooleanVar(value=True)

    def _create_profile():
        profile = prompt_for_profile()
        if profile:
            profiles = load_profiles()
            profiles[profile['name']] = profile
            save_profiles(profiles)

    def _on_profile_selected(profile):
        nonlocal _selected_profile
        _selected_profile = profile
        active_profile_text.set(f"Active Profile: {profile.get('name', '—')}")
        save_last_used_profile(profile["name"])  # Record selection

    def _choose_and_tag_folder():
        if not _selected_profile:
            messagebox.showwarning("No Profile Selected", "Please select a profile first.")
            return
        path = filedialog.askdirectory(title="Choose Folder to Tag")
        if path:
            print("[GUI DEBUG] No passphrase needed - using passphrase-less signing")
            sign_images_in_folder(path, _selected_profile, open_folder=open_folder_var.get())

    def on_verify_signature():
        img_path = filedialog.askopenfilename(title="Select image to verify", filetypes=[("JPEG", "*.jpg *.jpeg")])
        if img_path:
            if not _selected_profile:
                messagebox.showwarning("Verification Failed", "No active profile selected. Please select a profile first.")
                return
            try:
                # Use detailed verification to get more information
                result = VerificationService.verify_with_profile_detailed(img_path, _selected_profile, debug=True)
                
                if result["is_valid"]:
                    messagebox.showinfo("Verified", "This image is authentic and unaltered.")
                else:
                    # Show detailed error message
                    error_msg = "This image signature could not be verified.\n\n"
                    
                    if result["error_message"]:
                        error_msg += f"Reason: {result['error_message']}\n\n"
                    
                    if not result.get("gpg_key_match", True) and result["contact_info"]:
                        embedded_email = result["contact_info"].get("email", "Unknown")
                        profile_email = result["provided_profile"].get("email") or result["provided_profile"].get("gpg_key", "Unknown")
                        error_msg += "GPG Key Comparison:\n"
                        error_msg += f"• Image signed with: {embedded_email}\n"
                        error_msg += f"• Your profile uses: {profile_email}\n\n"
                        error_msg += "Tip: Select a profile with the matching GPG key/email.\n\n"
                    
                    if not result["profile_match"] and result["embedded_profile"]:
                        embedded = result["embedded_profile"]
                        provided = result["provided_profile"]
                        error_msg += "Profile Comparison:\n"
                        error_msg += f"• Image Author: {embedded.get('author', 'Unknown')}\n"
                        error_msg += f"• Image Copyright: {embedded.get('copyright', 'Unknown')}\n"
                        error_msg += f"• Image License: {embedded.get('license', 'Unknown')}\n\n"
                        error_msg += f"• Your Profile Author: {provided.get('author', 'Unknown')}\n"
                        error_msg += f"• Your Profile Copyright: {provided.get('copyright', 'Unknown')}\n"
                        error_msg += f"• Your Profile License: {provided.get('license', 'Unknown')}\n\n"
                    
                    if result.get("gpg_key_match", True) and result.get("profile_match", True):
                        error_msg += "The profile data matches, but the signature verification failed.\n"
                        error_msg += "This may indicate the image has been tampered with.\n\n"
                    
                    error_msg += "Tip: Use 'View Signature' to see the image's embedded information."
                    
                    messagebox.showwarning("Not Verified", error_msg)
                    
            except Exception as e:
                messagebox.showerror("Verification Failed", str(e))
        else:
            messagebox.showwarning("Verification Failed", "No image selected.")

    def view_contact_metadata():
        """View embedded contact information from image metadata"""
        img_path = filedialog.askopenfilename(
            title="Select image to view contact info", 
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif")]
        )
        if not img_path:
            return
            
        try:
            # Extract metadata from the image
            metadata = extract_profile_metadata(img_path)
            
            if not metadata or len(metadata) <= 1:  # Only has_signature field
                messagebox.showinfo("No Metadata", "No contact information found in this image.")
                return
            
            # Create a window to display the contact information
            contact_window = tk.Toplevel(root)
            contact_window.title("Image Contact Information")
            contact_window.geometry("400x300")
            contact_window.resizable(True, True)
            
            # Header
            ttk.Label(contact_window, text="📧 Embedded Contact Information", 
                     font=("Segoe UI", 12, "bold")).pack(pady=10)
            
            # Contact information display
            contact_frame = ttk.Frame(contact_window)
            contact_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            
            contact_text = tk.Text(contact_frame, wrap="word", font=("Segoe UI", 10))
            scrollbar = ttk.Scrollbar(contact_frame, orient="vertical", command=contact_text.yview)
            contact_text.configure(yscrollcommand=scrollbar.set)
            
            # Format and insert the contact information
            contact_info = format_contact_info(metadata)
            contact_text.insert("1.0", contact_info)
            
            # Add signature status if available
            if metadata.get('has_signature'):
                contact_text.insert("end", "\n\n🔐 Digital Signature: Present")
            else:
                contact_text.insert("end", "\n\n🔐 Digital Signature: Not found")
            
            contact_text.configure(state="disabled")
            contact_text.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not read contact information:\n{e}")

    def select_suspected_copy():
        """Step 1: Select the suspected copy image to keep in memory"""
        nonlocal _selected_suspected_copy
        
        if not COMPARISON_AVAILABLE:
            messagebox.showerror("Feature Unavailable", "Image comparison features not available. Please install OpenCV and NumPy.")
            return
            
        suspected_file = filedialog.askopenfilename(
            title="Select Suspected Copy Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif")]
        )
        
        if suspected_file:
            _selected_suspected_copy = suspected_file
            status_text.set(f"Comparing: {suspected_file}")
            
            # Dynamically resize window based on path length
            path_length = len(suspected_file)
            # Calculate required width: base width + extra width for path
            base_width = 450  # minimum width
            char_width = 8    # approximate pixels per character
            required_width = max(base_width, min(1200, base_width + (path_length - 50) * char_width))
            
            current_geometry = root.geometry()
            current_height = current_geometry.split('x')[1].split('+')[0]
            root.geometry(f"{required_width}x{current_height}")
            
            print(f"DEBUG: Selected suspected copy: {suspected_file}")
            print(f"DEBUG: Resized window to {required_width} pixels wide")
            
            # STEP 1: Check if file already has a valid signature
            if _selected_profile:
                try:
                    signature_valid = VerificationService.verify_with_profile(suspected_file, _selected_profile, debug=True)
                    if signature_valid:
                        # File has valid signature - no need for folder comparison
                        status_text.set(f"✅ Verified: {suspected_file}")
                        
                        # Create verification results window
                        results_window = tk.Toplevel(root)
                        results_window.title("Signature Verification Results")
                        results_window.geometry("600x500")
                        results_window.resizable(True, True)
                        
                        # Create main container
                        main_frame = ttk.Frame(results_window)
                        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
                        
                        # Create scrollable text widget (takes up most space)
                        text_frame = ttk.Frame(main_frame)
                        text_frame.pack(fill="both", expand=True, pady=(0, 10))
                        
                        results_text = tk.Text(text_frame, wrap="word", font=("Consolas", 10))
                        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=results_text.yview)
                        results_text.configure(yscrollcommand=scrollbar.set)
                        
                        results_text.pack(side="left", fill="both", expand=True)
                        scrollbar.pack(side="right", fill="y")
                        
                        # Create button frame at bottom (fixed height, always visible)
                        button_frame_bottom = ttk.Frame(main_frame)
                        button_frame_bottom.pack(fill="x", side="bottom")
                        
                        # Add verification results
                        results_content = f"SIGNATURE VERIFICATION RESULTS\n"
                        results_content += f"=" * 50 + "\n\n"
                        results_content += f"✅ FILE IS AUTHENTIC AND VERIFIED\n\n"
                        results_content += f"File: {os.path.basename(suspected_file)}\n"
                        results_content += f"Full Path: {suspected_file.replace('\\', '/')}\n\n"
                        results_content += f"VERIFICATION STATUS:\n"
                        results_content += f"• Embedded signature: ✅ Valid\n"
                        results_content += f"• Digital integrity: ✅ Confirmed\n"
                        results_content += f"• Copyright status: ✅ Legitimate original\n\n"
                        
                        # Add copyright information from profile
                        results_content += f"COPYRIGHT INFORMATION:\n"
                        
                        # Get copyright date from image metadata
                        copyright_datetime = extract_creation_datetime(suspected_file)
                        copyright_date = copyright_datetime.strftime("%Y-%m-%d")
                        copyright_year = copyright_datetime.year
                        
                        results_content += f"• Author: {_selected_profile.get('author', 'Unknown')}\n"
                        results_content += f"• Copyright Owner: {_selected_profile.get('copyright', 'Unknown')}\n"
                        results_content += f"• Copyright Date: {copyright_date}\n"
                        results_content += f"• Email: {_selected_profile.get('email', 'Unknown')}\n"
                        results_content += f"• License: {_selected_profile.get('license', 'Unknown')}\n\n"
                        
                        results_content += f"CONCLUSION:\n"
                        results_content += f"This image contains a valid digital signature and is confirmed\n"
                        results_content += f"to be an authentic original.\n"
                        
                        results_text.insert("1.0", results_content)
                        results_text.configure(state="disabled")
                        
                        def generate_verification_pdf():
                            """Generate a PDF report with the same content as the verification results"""
                            base_name = os.path.splitext(suspected_file)[0]
                            return create_pdf_report(results_content, base_name, "verification")
                        
                        # Variable to store PDF path
                        pdf_file_path = None
                        
                        def open_pdf_report():
                            """Open the generated PDF report"""
                            if pdf_file_path and os.path.exists(pdf_file_path):
                                try:
                                    import subprocess
                                    import platform
                                    
                                    if platform.system() == 'Windows':
                                        os.startfile(pdf_file_path)
                                    elif platform.system() == 'Darwin':  # macOS
                                        subprocess.run(['open', pdf_file_path])
                                    else:  # Linux
                                        subprocess.run(['xdg-open', pdf_file_path])
                                        
                                except Exception as e:
                                    messagebox.showerror("Error", f"Failed to open PDF:\n{str(e)}")
                            else:
                                messagebox.showwarning("PDF Not Found", "PDF file not found. Please generate PDF first.")
                        
                        
                        # Automatically generate PDF report with same filename as image
                        if PDF_AVAILABLE:
                            try:
                                pdf_file_path = generate_verification_pdf()
                                if pdf_file_path:
                                    # Add Open PDF button only if PDF was successfully created
                                    ttk.Button(button_frame_bottom, text="📖 Open PDF", command=open_pdf_report).pack(side="left", padx=(0, 10))
                            except Exception as e:
                                print(f"Failed to auto-generate PDF: {e}")
                        
                        ttk.Button(button_frame_bottom, text="❌ Close", command=results_window.destroy).pack(side="right")
                        
                        print(f"DEBUG: File has valid signature - no folder comparison needed")
                        return  # Exit early - no need for folder comparison
                        
                    else:
                        print(f"DEBUG: No valid signature found - will need folder comparison")
                        status_text.set(f"No signature - Ready to compare: {os.path.basename(suspected_file)}")
                        
                except Exception as e:
                    print(f"DEBUG: Error checking signature: {e}")
                    status_text.set(f"Signature check failed - Ready to compare: {os.path.basename(suspected_file)}")
            else:
                print(f"DEBUG: No profile selected - cannot verify signatures")
                status_text.set(f"No profile - Ready to compare: {os.path.basename(suspected_file)}")

    def compare_against_folder():
        """Step 2: Select folder and automatically trigger comparison"""
        nonlocal _selected_suspected_copy
        
        if not _selected_suspected_copy:
            messagebox.showwarning("No Image Selected", "Please select a suspected copy image first.")
            return
            
        if not COMPARISON_AVAILABLE:
            messagebox.showerror("Feature Unavailable", "Image comparison features not available. Please install OpenCV and NumPy.")
            return
            
        folder_path = filedialog.askdirectory(title="Select Folder with Copyrighted Images to Compare Against")
        
        if not folder_path:
            return
            
        # Automatically trigger comparison
        print(f"DEBUG: Comparing {_selected_suspected_copy} against folder: {folder_path}")
        
        # Create results window
        results_window = tk.Toplevel(root)
        results_window.title("Copyright Verification Results")
        results_window.geometry("800x600")
        results_window.resizable(True, True)
        
        # Create scrollable text widget
        text_frame = ttk.Frame(results_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        results_text = tk.Text(text_frame, wrap="word", font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=results_text.yview)
        results_text.configure(yscrollcommand=scrollbar.set)
        
        results_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Start with basic info
        results_content = f"COPYRIGHT VERIFICATION REPORT\n"
        results_content += f"=" * 50 + "\n\n"
        results_content += f"Suspected Copy: {os.path.basename(_selected_suspected_copy)}\n"
        results_content += f"Full Path: {_selected_suspected_copy.replace('\\', '/')}\n"
        results_content += f"Comparing Against: {folder_path}\n\n"
        
        results_text.insert("1.0", results_content)
        results_text.configure(state="disabled")
        results_text.update()
        
        # Perform the comparison
        perform_folder_comparison(_selected_suspected_copy, folder_path, results_text, results_window)

    def perform_folder_comparison(suspected_file, folder_path, results_widget, results_window):
        """Perform the actual comparison against all images in the folder"""
        try:
            results_widget.configure(state="normal")
            results_widget.insert("end", "SCANNING FOLDER FOR MATCHES...\n")
            results_widget.insert("end", "-" * 30 + "\n")
            results_widget.configure(state="disabled")
            results_widget.update()
            
            image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')
            found_matches = []
            total_files = 0
            
            # Count total files first
            for root_dir, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(image_extensions):
                        total_files += 1
            
            if total_files == 0:
                results_widget.configure(state="normal")
                results_widget.insert("end", "❌ No image files found in the selected folder\n")
                results_widget.configure(state="disabled")
                return
                
            results_widget.configure(state="normal")
            results_widget.insert("end", f"Found {total_files} image files to compare...\n\n")
            results_widget.configure(state="disabled")
            results_widget.update()
            
            current_file = 0
            
            # Compare against each image
            for root_dir, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(image_extensions):
                        current_file += 1
                        full_path = os.path.join(root_dir, file).replace('\\', '/')
                        
                        try:
                            # Update progress
                            results_widget.configure(state="normal")
                            results_widget.insert("end", f"Comparing {current_file}/{total_files}: {file}...\n")
                            results_widget.configure(state="disabled")
                            results_widget.see("end")
                            results_widget.update()
                            
                            # Compare with suspected copy
                            if image_comparator:
                                result = image_comparator.compare_images(suspected_file, full_path)
                                
                                if result.confidence_score > 0.7:  # Threshold for potential match
                                    match_info = {
                                        'file': file,
                                        'path': full_path,
                                        'confidence': result.confidence_score,
                                        'result': result
                                    }
                                    found_matches.append(match_info)
                                    
                                    results_widget.configure(state="normal")
                                    results_widget.insert("end", f"🎯 POTENTIAL MATCH FOUND!\n")
                                    results_widget.insert("end", f"   Confidence: {result.confidence_score:.2f}\n")
                                    results_widget.insert("end", f"   File: {file}\n\n")
                                    results_widget.configure(state="disabled")
                                    results_widget.see("end")
                                    results_widget.update()
                                    
                        except Exception as e:
                            print(f"Error comparing {full_path}: {e}")
                            continue
            
            # Show final results
            results_widget.configure(state="normal")
            results_widget.insert("end", f"\n" + "=" * 50 + "\n")
            results_widget.insert("end", f"FINAL RESULTS\n")
            results_widget.insert("end", f"=" * 50 + "\n\n")
            
            if found_matches:
                # Sort by confidence
                found_matches.sort(key=lambda x: x['confidence'], reverse=True)
                
                results_widget.insert("end", f"🔍 Found {len(found_matches)} potential matches:\n\n")
                for i, match in enumerate(found_matches, 1):
                    results_widget.insert("end", f"{i}. {match['file']}\n")
                    results_widget.insert("end", f"   Confidence: {match['confidence']:.2f}\n")
                    results_widget.insert("end", f"   Location: {match['path']}\n")
                    
                    # Check for signature in the original
                    try:
                        if _selected_profile:
                            sig_result = VerificationService.verify_with_profile(match['path'], _selected_profile)
                            if sig_result:
                                results_widget.insert("end", f"   Copyright: ✅ Verified signature\n")
                            else:
                                results_widget.insert("end", f"   Copyright: ❌ No signature\n")
                        else:
                            results_widget.insert("end", f"   Copyright: ⚠️ No profile to verify\n")
                    except:
                        results_widget.insert("end", f"   Copyright: ⚠️ Could not verify\n")
                    
                    results_widget.insert("end", "\n")
            else:
                results_widget.insert("end", "❌ No significant matches found\n")
                results_widget.insert("end", "The suspected image does not appear to match any images in the selected folder.\n")
            
            results_widget.configure(state="disabled")
            results_widget.see("end")
            
            # Add buttons at the bottom
            button_frame_bottom = ttk.Frame(results_window)
            button_frame_bottom.pack(fill="x", padx=10, pady=(0, 10))
            
            # Variable to store PDF path
            comparison_pdf_path = None
            
            def open_comparison_pdf():
                """Open the generated comparison PDF report"""
                if comparison_pdf_path and os.path.exists(comparison_pdf_path):
                    try:
                        import subprocess
                        import platform
                        
                        if platform.system() == 'Windows':
                            os.startfile(comparison_pdf_path)
                        elif platform.system() == 'Darwin':  # macOS
                            subprocess.run(['open', comparison_pdf_path])
                        else:  # Linux
                            subprocess.run(['xdg-open', comparison_pdf_path])
                            
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to open PDF:\n{str(e)}")
                else:
                    messagebox.showwarning("PDF Not Found", "PDF file not found. Please try again.")
            
            def select_new_folder():
                # Allow user to compare against a different folder
                compare_against_folder()
            
            # Only generate PDF report if matches were found
            if found_matches and PDF_AVAILABLE:
                try:
                    # Create filtered content for PDF containing only match details
                    def create_match_report_content():
                        # Ensure matches are sorted by confidence (highest first)
                        sorted_matches = sorted(found_matches, key=lambda x: x['confidence'], reverse=True)
                        
                        content = f"IMAGE COMPARISON RESULTS\n"
                        content += f"=" * 50 + "\n\n"
                        content += f"Suspected Image: {os.path.basename(suspected_file)}\n"
                        content += f"Full Path: {suspected_file.replace('\\', '/')}\n\n"
                        content += f"MATCHES FOUND: {len(sorted_matches)}\n"
                        content += f"(Listed in decreasing order of confidence)\n"
                        content += f"=" * 30 + "\n\n"
                        
                        for i, match in enumerate(sorted_matches, 1):
                            content += f"MATCH #{i} (Confidence: {match['confidence']:.2f})\n"
                            content += f"-" * 30 + "\n"
                            content += f"• File: {match['file']}\n"
                            content += f"• Confidence Score: {match['confidence']:.2f}\n"
                            content += f"• Location: {match['path']}\n"
                            
                            # Check for signature in the original
                            try:
                                if _selected_profile:
                                    sig_result = VerificationService.verify_with_profile(match['path'], _selected_profile)
                                    if sig_result:
                                        content += f"• Copyright: ✅ Verified signature\n"
                                    else:
                                        content += f"• Copyright: ❌ No signature\n"
                                else:
                                    content += f"• Copyright: ⚠️ No profile to verify\n"
                            except:
                                content += f"• Copyright: ⚠️ Could not verify\n"
                            
                            content += "\n"
                        
                        content += f"ANALYSIS SUMMARY\n"
                        content += f"=" * 20 + "\n"
                        content += f"Matches detected: {len(sorted_matches)}\n"
                        content += f"Highest confidence: {max(match['confidence'] for match in sorted_matches):.2f}\n"
                        content += f"Lowest confidence: {min(match['confidence'] for match in sorted_matches):.2f}\n"
                        
                        return content
                    
                    filtered_content = create_match_report_content()
                    base_name = os.path.splitext(suspected_file)[0]
                    comparison_pdf_path = create_pdf_report(filtered_content, base_name, "comparison")
                    if comparison_pdf_path:
                        # Add Open PDF button only if matches found and PDF was successfully created
                        ttk.Button(button_frame_bottom, text="📖 Open PDF", command=open_comparison_pdf).pack(side="left", padx=(0, 10))
                except Exception as e:
                    print(f"Failed to auto-generate comparison PDF: {e}")
            
            ttk.Button(button_frame_bottom, text="� Compare Against Different Folder", command=select_new_folder).pack(side="left", padx=(0, 10))
            ttk.Button(button_frame_bottom, text="❌ Close", command=results_window.destroy).pack(side="right")
            
        except Exception as e:
            results_widget.configure(state="normal")
            results_widget.insert("end", f"ERROR during comparison: {str(e)}\n")
            results_widget.configure(state="disabled")

    ttk.Button(button_frame, text="➕ Create Profile", command=_create_profile).pack(pady=5, fill="x", padx=20)
    ttk.Button(button_frame, text="🗂 Browse Profiles", command=lambda: launch_profile_browser(root, _on_profile_selected)).pack(pady=5,
                                                                                                                        fill="x",
                                                                                                                        padx=20)
    ttk.Button(button_frame, text="📁 Tag Folder", command=_choose_and_tag_folder).pack(pady=5, fill="x", padx=20)
    ttk.Button(button_frame, text="🔍 View Signature", command=view_embedded_signature).pack(pady=5, fill="x", padx=20)
    ttk.Button(button_frame, text="📧 View Contact Info", command=view_contact_metadata).pack(pady=5, fill="x", padx=20)
    ttk.Checkbutton(button_frame, text="Open folder after tagging", variable=open_folder_var).pack(pady=5)
    ttk.Button(button_frame, text="✅ Verify Signature", command=on_verify_signature).pack(pady=5, fill="x", padx=20)
    
    # Copyright Protection Section
    copyright_frame = ttk.LabelFrame(button_frame, text="Copyright Protection", padding=5)
    copyright_frame.pack(pady=10, fill="x", padx=20)
    
    if COMPARISON_AVAILABLE and copyright_db is not None:
        ttk.Button(copyright_frame, text="🔍 Select Suspected Copy", command=select_suspected_copy).pack(pady=2, fill="x")
        ttk.Button(copyright_frame, text="📂 Compare Against Folder", command=compare_against_folder).pack(pady=2, fill="x")
        
        # Status display (using the global status_text variable)
        status_label = ttk.Label(copyright_frame, textvariable=status_text, font=("Segoe UI", 8), foreground="#666")
        status_label.pack(pady=(5, 0))
    else:
        ttk.Label(copyright_frame, text="⚠️ Copyright verification unavailable", foreground="red").pack(pady=5)
        ttk.Label(copyright_frame, text="Install OpenCV and NumPy to enable", font=("Segoe UI", 8)).pack()
        
    ttk.Button(button_frame, text="❌ Exit", command=root.destroy).pack(pady=15)

    root.mainloop()


if __name__ == "__main__":
    launch_gui()
