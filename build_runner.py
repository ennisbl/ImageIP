#!/usr/bin/env python3
"""
Simple runner for external_builder.py to avoid setuptools conflicts.
"""

import sys
import os
import re
import shutil
import subprocess
import json
from pathlib import Path

def get_version_from_setup():
    """Extract VERSION from setup.py without importing it."""
    setup_path = Path(__file__).parent / "setup.py"
    with open(setup_path, 'r') as f:
        content = f.read()
    
    # Find VERSION = "x.x.x" pattern
    version_match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
    if version_match:
        return version_match.group(1)
    else:
        raise ValueError("Could not find VERSION in setup.py")

class SimpleBuilder:
    def __init__(self, source_repo_path, build_workspace_path=None):
        self.source_path = Path(source_repo_path).resolve()
        
        if build_workspace_path:
            self.build_workspace = Path(build_workspace_path).resolve()
        else:
            # Create build workspace as sibling to source repo
            self.build_workspace = self.source_path.parent / "ImageIP-Build"
        
        # Define build structure
        self.releases = self.build_workspace / "releases"
        self.build_artifacts = self.build_workspace / "build-artifacts"
        
        # Get version
        self.version = get_version_from_setup()

    def prepare_workspace(self):
        """Prepare the clean build workspace"""
        print(f"🚀 Starting ImageIP v{self.version} Clean Build Process")
        print("=" * 55)
        
        print("\n📁 Setting up build workspace...")
        
        # Create build directories
        for dir_path in [self.build_workspace, self.releases, self.build_artifacts]:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✓ {dir_path}")
        
        # Copy source files to build workspace
        source_copy = self.build_workspace / "source"
        if source_copy.exists():
            shutil.rmtree(source_copy)
        
        print(f"\n📋 Copying source files...")
        print(f"   From: {self.source_path}")
        print(f"   To:   {source_copy}")
        
        shutil.copytree(self.source_path, source_copy, 
                       ignore=shutil.ignore_patterns(
                           '*.git*', '__pycache__', '*.pyc', 
                           'build', 'dist', '*.egg-info',
                           '.venv', 'venv'
                       ))
        
        return source_copy

    def create_release_package(self):
        """Create final release package"""
        print(f"\n📦 Creating release package for v{self.version}...")
        
        release_dir = self.releases / f"ImageIP-v{self.version}-Release"
        
        if release_dir.exists():
            shutil.rmtree(release_dir)
        release_dir.mkdir(parents=True)
        
        # Copy source files
        print("   📋 Packaging source code...")
        source_pkg = release_dir / "source"
        shutil.copytree(self.source_path, source_pkg,
                       ignore=shutil.ignore_patterns(
                           '*.git*', '__pycache__', '*.pyc',
                           'build', 'dist', '*.egg-info',
                           '.venv', 'venv'
                       ))
        
        # Create release info
        release_info = {
            "name": "ImageIP",
            "version": self.version,
            "platform": sys.platform,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "files": {
                "source": "Complete source code",
                "README.md": "Installation and usage instructions",
                "LICENSE": "MIT License",
                "requirements.txt": "Python dependencies"
            }
        }
        
        # Write release info
        with open(release_dir / "release-info.json", 'w') as f:
            json.dump(release_info, f, indent=2)
        
        print(f"   ✅ Release package created: {release_dir}")
        
        return release_dir

    def build_all(self):
        """Complete build process"""
        try:
            # Prepare workspace
            source_copy = self.prepare_workspace()
            
            # Create release package
            release_dir = self.create_release_package()
            
            print(f"\n🎉 Build completed successfully!")
            print("=" * 55)
            print(f"📁 Release directory: {release_dir}")
            print(f"🏷️  Version: {self.version}")
            print(f"📦 Ready for upload to GitHub!")
            
            # List contents
            print(f"\n📋 Release contents:")
            for item in release_dir.iterdir():
                if item.is_file():
                    size = item.stat().st_size
                    print(f"   📄 {item.name} ({size:,} bytes)")
                else:
                    print(f"   📁 {item.name}/")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Build failed: {e}")
            return False

if __name__ == "__main__":
    # Create and run builder
    current_dir = Path(__file__).parent
    builder = SimpleBuilder(current_dir)
    
    success = builder.build_all()
    if not success:
        sys.exit(1)
