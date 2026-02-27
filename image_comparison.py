"""
image_comparison.py — Advanced image comparison for copyright verification.

This module provides sophisticated image comparison capabilities that can identify
if a transformed image is derived from an original copyrighted image, even when
embedded signatures are lost during transformation processes like scaling,
compression, cropping, or format conversion.

The system uses multiple complementary techniques:
1. Perceptual hashing for scale/compression invariance
2. SIFT feature matching for geometric transformations
3. Color histogram analysis for color space changes
4. DCT coefficient comparison for frequency domain analysis
5. Edge detection patterns for structural similarity

Key Features:
- Works with images that have been scaled, cropped, compressed, or filtered
- Provides confidence scores for match quality
- Handles multiple image formats and color spaces
- Robust against common image transformations
- Integrates with existing ImageIP signature system

Author: Bernard Ennis
License: MIT
"""

import cv2
import numpy as np
import hashlib
from typing import Tuple, Dict, List, Optional
from dataclasses import dataclass
from PIL import Image, ImageFilter
import json
import os
from pathlib import Path

@dataclass
class ComparisonResult:
    """Results from image comparison analysis."""
    is_match: bool
    confidence_score: float
    perceptual_hash_similarity: float
    feature_match_count: int
    color_histogram_similarity: float
    edge_similarity: float
    transformation_detected: str
    details: Dict

class ImageComparator:
    """Advanced image comparison engine for copyright verification."""
    
    def __init__(self):
        """Initialize the image comparator with default parameters."""
        self.sift = cv2.SIFT_create()
        self.flann_index_kdtree = 1
        self.index_params = dict(algorithm=self.flann_index_kdtree, trees=5)
        self.search_params = dict(checks=50)
        self.flann = cv2.FlannBasedMatcher(self.index_params, self.search_params)
        
        # Thresholds for different comparison methods
        self.thresholds = {
            'perceptual_hash': 0.8,
            'feature_matches': 10,
            'color_histogram': 0.7,
            'edge_similarity': 0.6,
            'overall_confidence': 0.7
        }
    
    def compute_perceptual_hash(self, image: np.ndarray, hash_size: int = 16) -> str:
        """
        Compute perceptual hash using DCT.
        This hash is resistant to scaling, compression, and minor modifications.
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Resize to standard size for consistency
        resized = cv2.resize(gray, (hash_size * 4, hash_size * 4))
        
        # Apply DCT
        dct = cv2.dct(np.float32(resized))
        
        # Take top-left corner (low frequencies)
        dct_low_freq = dct[:hash_size, :hash_size]
        
        # Calculate median
        median = np.median(dct_low_freq)
        
        # Create binary hash based on median
        binary_hash = dct_low_freq > median
        
        # Convert to hex string
        hash_string = ''
        for row in binary_hash:
            for pixel in row:
                hash_string += '1' if pixel else '0'
        
        # Convert binary to hex
        hex_hash = hex(int(hash_string, 2))[2:].zfill(len(hash_string) // 4)
        return hex_hash
    
    def compare_perceptual_hashes(self, hash1: str, hash2: str) -> float:
        """Compare two perceptual hashes and return similarity score (0-1)."""
        if len(hash1) != len(hash2):
            return 0.0
        
        # Convert hex to binary
        bin1 = bin(int(hash1, 16))[2:].zfill(len(hash1) * 4)
        bin2 = bin(int(hash2, 16))[2:].zfill(len(hash2) * 4)
        
        # Calculate Hamming distance
        hamming_distance = sum(c1 != c2 for c1, c2 in zip(bin1, bin2))
        max_distance = len(bin1)
        
        # Return similarity (1 - normalized hamming distance)
        similarity = 1.0 - (hamming_distance / max_distance)
        return similarity
    
    def extract_sift_features(self, image: np.ndarray) -> Tuple[List, np.ndarray]:
        """Extract SIFT keypoints and descriptors."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        keypoints, descriptors = self.sift.detectAndCompute(gray, None)
        return keypoints, descriptors
    
    def match_features(self, desc1: np.ndarray, desc2: np.ndarray) -> List:
        """Match SIFT features between two images."""
        if desc1 is None or desc2 is None or len(desc1) < 2 or len(desc2) < 2:
            return []
        
        try:
            matches = self.flann.knnMatch(desc1, desc2, k=2)
            
            # Apply Lowe's ratio test
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)
            
            return good_matches
        except Exception:
            return []
    
    def compute_color_histogram(self, image: np.ndarray, bins: int = 32) -> np.ndarray:
        """Compute color histogram for the image."""
        if len(image.shape) == 3:
            # Convert BGR to HSV for better color representation
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1, 2], None, [bins, bins, bins], [0, 180, 0, 256, 0, 256])
        else:
            hist = cv2.calcHist([image], [0], None, [bins], [0, 256])
        
        # Normalize histogram
        cv2.normalize(hist, hist)
        return hist.flatten()
    
    def compare_histograms(self, hist1: np.ndarray, hist2: np.ndarray) -> float:
        """Compare two histograms using correlation."""
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    
    def compute_edge_features(self, image: np.ndarray) -> np.ndarray:
        """Compute edge features using Canny edge detection."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Resize to standard size for comparison
        edges_resized = cv2.resize(edges, (64, 64))
        
        return edges_resized.flatten()
    
    def compare_edge_features(self, edges1: np.ndarray, edges2: np.ndarray) -> float:
        """Compare edge features using normalized correlation."""
        # Normalize the edge vectors
        norm1 = np.linalg.norm(edges1)
        norm2 = np.linalg.norm(edges2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Compute normalized correlation
        correlation = np.dot(edges1, edges2) / (norm1 * norm2)
        return max(0.0, correlation)  # Ensure non-negative
    
    def detect_transformation_type(self, kp1: List, kp2: List, matches: List) -> str:
        """Detect the type of transformation between images."""
        if len(matches) < 4:
            return "insufficient_features"
        
        # Extract matched points
        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        
        try:
            # Try to find homography
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            
            if M is not None:
                # Analyze the transformation matrix
                det = np.linalg.det(M[:2, :2])
                
                if abs(det - 1.0) < 0.1:
                    return "similarity_transform"  # Rotation + uniform scaling + translation
                elif det > 0.5:
                    return "affine_transform"  # Non-uniform scaling, shearing
                else:
                    return "perspective_transform"  # Perspective distortion
            else:
                return "complex_transformation"
        except Exception:
            return "transformation_detection_failed"
    
    def compare_images(self, original_path: str, test_path: str) -> ComparisonResult:
        """
        Perform comprehensive comparison between original and test images.
        
        Args:
            original_path: Path to the original copyrighted image
            test_path: Path to the image to test for copyright match
            
        Returns:
            ComparisonResult with detailed analysis
        """
        # Load images with error handling
        try:
            original = cv2.imread(original_path)
            test = cv2.imread(test_path)
            
            if original is None:
                raise ValueError(f"Could not load original image: {original_path}")
            if test is None:
                raise ValueError(f"Could not load test image: {test_path}")
        except Exception as e:
            raise ValueError(f"Error loading images: {str(e)}")
        
        results = {}
        
        try:
            # 1. Perceptual hash comparison
            orig_hash = self.compute_perceptual_hash(original)
            test_hash = self.compute_perceptual_hash(test)
            perceptual_similarity = self.compare_perceptual_hashes(orig_hash, test_hash)
            results['perceptual_hash'] = {
                'original_hash': orig_hash,
                'test_hash': test_hash,
                'similarity': perceptual_similarity
            }
        except Exception as e:
            print(f"Warning: Perceptual hash comparison failed: {e}")
            perceptual_similarity = 0.0
            results['perceptual_hash'] = {'error': str(e), 'similarity': 0.0}
        
        try:
            # 2. SIFT feature matching
            kp1, desc1 = self.extract_sift_features(original)
            kp2, desc2 = self.extract_sift_features(test)
            matches = self.match_features(desc1, desc2)
            feature_match_count = len(matches)
            
            transformation_type = self.detect_transformation_type(kp1, kp2, matches)
            
            results['feature_matching'] = {
                'original_features': len(kp1) if kp1 else 0,
                'test_features': len(kp2) if kp2 else 0,
                'matches': feature_match_count,
                'transformation': transformation_type
            }
        except Exception as e:
            print(f"Warning: Feature matching failed: {e}")
            feature_match_count = 0
            transformation_type = "feature_matching_failed"
            results['feature_matching'] = {'error': str(e), 'matches': 0}
        
        try:
            # 3. Color histogram comparison
            orig_hist = self.compute_color_histogram(original)
            test_hist = self.compute_color_histogram(test)
            color_similarity = self.compare_histograms(orig_hist, test_hist)
            results['color_histogram'] = {
                'similarity': float(color_similarity)
            }
        except Exception as e:
            print(f"Warning: Color histogram comparison failed: {e}")
            color_similarity = 0.0
            results['color_histogram'] = {'error': str(e), 'similarity': 0.0}
        
        try:
            # 4. Edge feature comparison
            orig_edges = self.compute_edge_features(original)
            test_edges = self.compute_edge_features(test)
            edge_similarity = self.compare_edge_features(orig_edges, test_edges)
            results['edge_features'] = {
                'similarity': float(edge_similarity)
            }
        except Exception as e:
            print(f"Warning: Edge feature comparison failed: {e}")
            edge_similarity = 0.0
            results['edge_features'] = {'error': str(e), 'similarity': 0.0}
        
        # 5. Calculate overall confidence score
        confidence_components = [
            perceptual_similarity * 0.4,  # Perceptual hash is most reliable
            min(feature_match_count / 20.0, 1.0) * 0.3,  # Feature matching
            color_similarity * 0.2,  # Color histogram
            edge_similarity * 0.1  # Edge features
        ]
        
        overall_confidence = sum(confidence_components)
        
        # Determine if it's a match based on multiple criteria
        is_match = (
            perceptual_similarity >= self.thresholds['perceptual_hash'] or
            (feature_match_count >= self.thresholds['feature_matches'] and
             color_similarity >= self.thresholds['color_histogram']) or
            (perceptual_similarity >= 0.6 and 
             color_similarity >= 0.8 and 
             edge_similarity >= 0.7)
        )
        
        return ComparisonResult(
            is_match=is_match,
            confidence_score=overall_confidence,
            perceptual_hash_similarity=perceptual_similarity,
            feature_match_count=feature_match_count,
            color_histogram_similarity=float(color_similarity),
            edge_similarity=float(edge_similarity),
            transformation_detected=transformation_type,
            details=results
        )

class CopyrightDatabase:
    """Database for storing and managing copyright fingerprints."""
    
    def __init__(self, db_path: str = "profiles/copyright_db.json"):
        """Initialize the copyright database."""
        self.db_path = db_path
        self.comparator = ImageComparator()
        self.load_database()
    
    def load_database(self):
        """Load the copyright database from disk."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.db = json.load(f)
            except Exception:
                self.db = {}
        else:
            self.db = {}
    
    def save_database(self):
        """Save the copyright database to disk."""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.db, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving database: {e}")
    
    def register_original_image(self, image_path: str, owner_info: dict) -> str:
        """
        Register an original image in the copyright database.
        
        Args:
            image_path: Path to the original image
            owner_info: Dictionary with owner information (name, email, etc.)
            
        Returns:
            Unique fingerprint ID for the registered image
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Generate comprehensive fingerprint
        perceptual_hash = self.comparator.compute_perceptual_hash(image)
        color_hist = self.comparator.compute_color_histogram(image)
        edge_features = self.comparator.compute_edge_features(image)
        
        # Create unique fingerprint ID
        fingerprint_data = f"{perceptual_hash}_{image.shape}_{owner_info.get('email', '')}"
        fingerprint_id = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
        
        # Store in database
        entry = {
            'fingerprint_id': fingerprint_id,
            'original_path': os.path.abspath(image_path),
            'owner_info': owner_info,
            'perceptual_hash': perceptual_hash,
            'color_histogram': color_hist.tolist(),
            'edge_features': edge_features.tolist(),
            'image_dimensions': image.shape,
            'registration_date': str(np.datetime64('now'))
        }
        
        self.db[fingerprint_id] = entry
        self.save_database()
        
        return fingerprint_id
    
    def verify_image_copyright(self, test_image_path: str, 
                              min_confidence: float = 0.7) -> List[Dict]:
        """
        Check if a test image matches any registered copyrighted images.
        
        Args:
            test_image_path: Path to the image to verify
            min_confidence: Minimum confidence threshold for matches
            
        Returns:
            List of potential matches with details
        """
        matches = []
        
        for fingerprint_id, entry in self.db.items():
            try:
                # Check if original file still exists
                if not os.path.exists(entry['original_path']):
                    continue
                
                # Perform comparison
                result = self.comparator.compare_images(
                    entry['original_path'], 
                    test_image_path
                )
                
                if result.confidence_score >= min_confidence:
                    match_info = {
                        'fingerprint_id': fingerprint_id,
                        'owner_info': entry['owner_info'],
                        'original_path': entry['original_path'],
                        'comparison_result': result,
                        'registration_date': entry.get('registration_date', 'Unknown')
                    }
                    matches.append(match_info)
                    
            except Exception as e:
                print(f"Error comparing with {fingerprint_id}: {e}")
                continue
        
        # Sort by confidence score (highest first)
        matches.sort(key=lambda x: x['comparison_result'].confidence_score, reverse=True)
        
        return matches

    def has_registered_images(self) -> bool:
        """Check if the database has any registered images."""
        return len(self.db) > 0


def create_copyright_verification_report(comparison_result: ComparisonResult, 
                                       original_path: str, 
                                       test_path: str,
                                       owner_info: dict) -> str:
    """Create a detailed copyright verification report."""
    
    report = f"""
COPYRIGHT VERIFICATION REPORT
============================

ANALYSIS DATE: {np.datetime64('now')}

ORIGINAL IMAGE: {os.path.basename(original_path)}
TEST IMAGE: {os.path.basename(test_path)}

COPYRIGHT OWNER: {owner_info.get('name', 'Unknown')}
OWNER EMAIL: {owner_info.get('email', 'Unknown')}

VERIFICATION RESULT: {'MATCH CONFIRMED' if comparison_result.is_match else 'NO MATCH DETECTED'}
CONFIDENCE SCORE: {comparison_result.confidence_score:.3f}

DETAILED ANALYSIS:
-----------------
Perceptual Hash Similarity: {comparison_result.perceptual_hash_similarity:.3f}
Feature Matches Found: {comparison_result.feature_match_count}
Color Histogram Similarity: {comparison_result.color_histogram_similarity:.3f}
Edge Pattern Similarity: {comparison_result.edge_similarity:.3f}
Transformation Detected: {comparison_result.transformation_detected}

INTERPRETATION:
--------------
"""
    
    if comparison_result.is_match:
        report += """
✓ The test image appears to be derived from the registered original image.
✓ Multiple similarity metrics support this conclusion.
✓ This suggests potential copyright infringement if used without permission.
"""
    else:
        report += """
✗ The test image does not appear to be derived from the registered original.
✗ Insufficient similarity across multiple comparison metrics.
✗ This is likely a different image or heavily modified beyond recognition.
"""
    
    report += f"""
TECHNICAL DETAILS:
-----------------
{json.dumps(comparison_result.details, indent=2)}

This report was generated by ImageIP Copyright Verification System.
"""
    
    return report
