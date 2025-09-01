# Changelog

All notable changes to ImageIP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2025-09-01

### 🔧 Version Management Optimization

### Fixed
- **Version centralization**: Resolved setuptools import conflicts by keeping VERSION in setup.py
- **Import optimization**: Implemented file-reading approach to avoid circular imports
- **Build system stability**: Fixed external_builder.py to work without triggering setuptools
- **Cleaner architecture**: All modules now safely read version from setup.py without import issues

### Technical Improvements
- Centralized version management with setup.py as single source of truth
- Safe version reading without setuptools interference
- Improved module import reliability
- Enhanced build system compatibility

## [1.1.0] - 2025-09-01

### 🧹 Repository Cleanup & Professional Build System

### Added
- **External build system** for clean, professional builds
- **Repository cleanup** removing 50%+ build artifacts and clutter  
- **Enhanced .gitignore** to prevent future build pollution
- **Streamlined codebase** down to 19 essential files
- **Professional development workflow** with separated build environment
- **Reusable build scripts** that can be used for future versions

### Changed
- **Repository structure** now contains only essential source code and documentation
- **Build process** moved to external workspace to maintain clean repository
- **Version bumped** to 1.1.0 for the cleaned release

### Removed
- **Build artifacts** (build/, dist/, __pycache__, *.spec files)
- **Excessive documentation** (duplicate build guides, summary files)
- **Development scripts** moved to external build system
- **Version artifacts** and temporary files

### Technical Improvements
- **Clean git history** with proper separation of source vs. build
- **Faster repository cloning** due to reduced file count
- **Professional software development practices** implemented
- **Maintainable codebase** with clear organization

---

## [1.0.2] - 2025-09-01

### 🎉 Major Architecture Overhaul & Documentation Enhancement

### Added
- **Comprehensive documentation** with sequence diagrams using Mermaid
- **Enhanced docstrings** for all modules with detailed function documentation
- **Professional README** with architecture overview and troubleshooting guide
- **Modular architecture** with clear separation of concerns
- **Signature viewing functionality** with GUI interface
- **Signature verification system** with detailed error reporting
- **Cross-platform file metadata support** for transparent images
- **Automatic GPG key generation** with no-passphrase support
- **Base64 signature encoding** for reliable EXIF storage

### Changed
- **Refactored monolithic code** into clean modular components
- **Improved GUI layout** with better user experience
- **Enhanced error handling** throughout the application
- **Streamlined signing workflow** with better progress indication
- **Updated dependency management** with platform-specific requirements

### Removed
- **20+ unnecessary files** including debug scripts, test files, and utilities
- **Legacy monolithic imageip.py** replaced with modular architecture
- **Redundant functionality** and obsolete code paths
- **Temporary files** and development artifacts

### Security
- **2048-bit RSA keys** for long-term signature validity
- **SHA-256 cryptographic hashing** for image fingerprinting
- **Passphrase-free key generation** for improved usability
- **Automatic trust model** for streamlined verification

### Technical
- **Complete module reorganization** with clear responsibilities
- **Standardized attribution metadata** formatting
- **Centralized signature utilities** for consistent handling
- **Cross-platform GPG integration** with automatic home detection
- **Comprehensive error handling** and debug output

### Documentation
- **Architecture diagrams** showing component relationships
- **4 detailed sequence diagrams** covering core workflows:
  - Image Signing Process
  - Profile Creation & Key Generation
  - Signature Verification Process
  - Signature Viewing Process
- **Module reference** with function listings
- **Configuration guide** for profile and GPG setup
- **Troubleshooting section** for common issues
- **Technical details** explaining cryptographic approach

## [1.0.1] - Previous Release

### Features
- Basic image signing functionality
- Profile management system
- GPG integration
- EXIF metadata embedding

## [1.0.0] - Initial Release

### Features
- Core image signing capability
- Basic GUI interface
- Profile creation
- JPEG format support

---

### Legend
- 🎉 Major Feature
- ✨ Enhancement
- 🐛 Bug Fix
- 🔒 Security
- 📚 Documentation
- 🧹 Code Cleanup
