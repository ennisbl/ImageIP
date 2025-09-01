#!/usr/bin/env python3
"""
External Build System for ImageIP
Creates a clean build environment outside the source repository

Usage:
    python external_builder.py [source_path] [build_path]

Example:
    python external_builder.py C:\\Users\\majik\\Code\\ImageIP C:\\Users\\majik\\Code\\ImageIP-Build
"""
import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

class ImageIPBuilder:
    def __init__(self, source_repo_path, build_workspace_path=None):
        self.source_path = Path(source_repo_path).resolve()
        
        if build_workspace_path:
            self.build_workspace = Path(build_workspace_path).resolve()
        else:
            # Create build workspace next to the repo
            self.build_workspace = self.source_path.parent / "ImageIP-Build"
        
        self.build_source = self.build_workspace / "source"
        self.build_artifacts = self.build_workspace / "artifacts"
        self.releases = self.build_workspace / "releases"
        
        print(f"🏗️ Source Repository: {self.source_path}")
        print(f"🔧 Build Workspace: {self.build_workspace}")
    
    def setup_build_workspace(self):
        """Create clean build workspace"""
        print("\n🔧 Setting up build workspace...")
        
        # Remove old build workspace if it exists
        if self.build_workspace.exists():
            print(f"   Cleaning existing workspace: {self.build_workspace}")
            shutil.rmtree(self.build_workspace)
        
        # Create directory structure
        directories = [
            self.build_workspace,
            self.build_source,
            self.build_artifacts / "executables",
            self.build_artifacts / "packages", 
            self.build_artifacts / "source",
            self.releases
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"   Created: {directory.name}")
        
        print("✅ Build workspace ready")
    
    def copy_source_code(self):
        """Copy source code to build workspace"""
        print("\n📁 Copying source code...")
        
        # Files and folders to exclude from copying
        exclude_patterns = [
            "build", "dist", "__pycache__", ".git", ".venv", 
            "*.spec", "*.exe", "*.app", "*.dmg", ".pytest_cache",
            "build_release.py", "build_release.bat", "quick_build.py",
            "external_builder.py", "BUILD_GUIDE.md", "BUILD_SUMMARY.md"
        ]
        
        copied_files = 0
        for item in self.source_path.iterdir():
            # Skip hidden files except .gitignore
            if item.name.startswith('.') and item.name not in ['.gitignore']:
                continue
                
            # Skip excluded patterns
            if any(pattern in item.name for pattern in exclude_patterns):
                print(f"   Skipping: {item.name}")
                continue
            
            dest = self.build_source / item.name
            
            if item.is_file():
                shutil.copy2(item, dest)
                print(f"   Copied file: {item.name}")
                copied_files += 1
            elif item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
                print(f"   Copied folder: {item.name}")
                copied_files += 1
        
        print(f"✅ Source code copied ({copied_files} items)")
    
    def install_dependencies(self):
        """Install build dependencies"""
        print("\n📦 Installing dependencies...")
        
        # Install application dependencies
        requirements_file = self.build_source / "requirements.txt"
        if requirements_file.exists():
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ Application dependencies installed")
            else:
                print(f"   ⚠️ Some dependencies may have failed: {result.stderr}")
        
        # Install build tools
        build_deps = ["pyinstaller>=5.0", "setuptools", "wheel"]
        cmd = [sys.executable, "-m", "pip", "install"] + build_deps
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Build tools installed")
        else:
            print(f"   ❌ Build tools installation failed: {result.stderr}")
            raise Exception("Failed to install build dependencies")
    
    def build_executable(self, platform="Windows"):
        """Build platform-specific executable"""
        print(f"\n🔨 Building {platform} executable...")
        
        # Change to build source directory
        original_cwd = os.getcwd()
        os.chdir(self.build_source)
        
        try:
            # Build command
            cmd = [
                "pyinstaller",
                "--onefile",
                "--windowed",
                "--name", f"ImageIP-v1.1.0-{platform}",
                "--distpath", str(self.build_artifacts / "executables"),
                "--workpath", str(self.build_workspace / "temp"),
                "--clean"
            ]
            
            # Add icon if available
            icon_files = ["assets/ImageIP_logo.ico", "assets/ImageIP_logo.png", "assets/icon.ico"]
            for icon in icon_files:
                icon_path = self.build_source / icon
                if icon_path.exists():
                    cmd.extend(["--icon", str(icon_path)])
                    print(f"   Using icon: {icon}")
                    break
            
            # Add data files
            if (self.build_source / "assets").exists():
                cmd.extend(["--add-data", f"assets{os.pathsep}assets"])
                print("   Including assets folder")
            
            # Add hidden imports for better compatibility
            hidden_imports = [
                "PIL._tkinter_finder", "tkinter", "tkinter.ttk", 
                "tkinter.messagebox", "tkinter.filedialog", "piexif", "gnupg"
            ]
            for imp in hidden_imports:
                cmd.extend(["--hidden-import", imp])
            
            cmd.append("main.py")
            
            print(f"   Running: {' '.join(cmd)}")
            
            # Run build
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Executable built successfully")
                
                # Check if executable was created
                exec_name = f"ImageIP-v1.1.0-{platform}.exe" if platform.lower() == "windows" else f"ImageIP-v1.1.0-{platform}"
                exec_path = self.build_artifacts / "executables" / exec_name
                if exec_path.exists():
                    size_mb = exec_path.stat().st_size / (1024 * 1024)
                    print(f"   📁 Executable: {exec_name} ({size_mb:.1f} MB)")
                
            else:
                print(f"❌ Build failed: {result.stderr}")
                raise Exception("PyInstaller build failed")
                
        finally:
            os.chdir(original_cwd)
    
    def build_packages(self):
        """Build Python packages"""
        print("\n📦 Building Python packages...")
        
        original_cwd = os.getcwd()
        os.chdir(self.build_source)
        
        try:
            # Source distribution
            cmd = [sys.executable, "setup.py", "sdist", 
                   "--dist-dir", str(self.build_artifacts / "packages")]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ Source distribution created")
            else:
                print(f"   ⚠️ Source distribution warning: {result.stderr}")
            
            # Wheel package
            cmd = [sys.executable, "setup.py", "bdist_wheel",
                   "--dist-dir", str(self.build_artifacts / "packages")]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ Wheel package created")
            else:
                print(f"   ⚠️ Wheel package warning: {result.stderr}")
                
        finally:
            os.chdir(original_cwd)
    
    def create_release_package(self):
        """Create final release package"""
        print("\n📦 Creating release package...")
        
        version = "1.1.0"
        release_dir = self.releases / f"ImageIP-v{version}-Release"
        
        if release_dir.exists():
            shutil.rmtree(release_dir)
        
        release_dir.mkdir(parents=True)
        
        # Copy executables
        if (self.build_artifacts / "executables").exists():
            exec_dir = release_dir / "executables"
            shutil.copytree(self.build_artifacts / "executables", exec_dir)
            print(f"   📱 Copied executables to: {exec_dir}")
        
        # Copy packages
        if (self.build_artifacts / "packages").exists():
            pkg_dir = release_dir / "packages"
            shutil.copytree(self.build_artifacts / "packages", pkg_dir)
            print(f"   📦 Copied packages to: {pkg_dir}")
        
        # Copy documentation
        docs = ["README.md", "CHANGELOG.md", "LICENSE", "RELEASE_NOTES.md"]
        for doc in docs:
            src = self.build_source / doc
            if src.exists():
                shutil.copy2(src, release_dir)
                print(f"   📄 Copied: {doc}")
        
        # Create release info
        release_info = {
            "name": "ImageIP",
            "version": version,
            "platform": sys.platform,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "files": {}
        }
        
        # List all created files
        for subdir in ["executables", "packages"]:
            path = release_dir / subdir
            if path.exists():
                release_info["files"][subdir] = [f.name for f in path.iterdir()]
        
        with open(release_dir / "release_info.json", 'w') as f:
            json.dump(release_info, f, indent=2)
        
        print(f"✅ Release package created: {release_dir}")
        return release_dir
    
    def cleanup_temp_files(self):
        """Clean up temporary build files"""
        print("\n🧹 Cleaning up temporary files...")
        
        temp_dirs = [
            self.build_workspace / "temp",
            self.build_source / "build",
            self.build_source / "__pycache__"
        ]
        
        cleaned = 0
        for temp_dir in temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                print(f"   Removed: {temp_dir.name}")
                cleaned += 1
        
        if cleaned == 0:
            print("   No temporary files to clean")
        else:
            print(f"✅ Cleanup completed ({cleaned} items removed)")
    
    def build_all(self):
        """Complete build process"""
        print("🚀 Starting ImageIP v1.1.0 Clean Build Process")
        print("=" * 55)
        
        try:
            self.setup_build_workspace()
            self.copy_source_code()
            self.install_dependencies()
            self.build_executable()
            self.build_packages()
            release_dir = self.create_release_package()
            self.cleanup_temp_files()
            
            print("\n" + "=" * 55)
            print("🎉 BUILD COMPLETED SUCCESSFULLY!")
            print(f"📁 Release files: {release_dir}")
            print("\n🎯 GitHub Release Assets to upload:")
            
            # List specific files to upload
            exec_dir = release_dir / "executables"
            pkg_dir = release_dir / "packages"
            
            if exec_dir.exists():
                for exe_file in exec_dir.iterdir():
                    print(f"   📱 {exe_file.name}")
            
            if pkg_dir.exists():
                for pkg_file in pkg_dir.iterdir():
                    print(f"   📦 {pkg_file.name}")
            
            print(f"\n📋 Complete release folder: {release_dir}")
            print("🚀 Ready for GitHub upload!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ BUILD FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main build script"""
    print("ImageIP External Build System v1.0")
    print("Keeps your repository clean by building in separate workspace")
    print("=" * 55)
    
    if len(sys.argv) > 1:
        source_path = sys.argv[1]
    else:
        # Default to ImageIP repo location
        default_path = r"C:\Users\majik\Code\ImageIP"
        print(f"Default source path: {default_path}")
        source_path = input(f"Enter ImageIP source path (or press Enter for default): ").strip()
        if not source_path:
            source_path = default_path
    
    if not Path(source_path).exists():
        print(f"❌ Source path does not exist: {source_path}")
        return 1
    
    # Optional custom build path
    if len(sys.argv) > 2:
        build_path = sys.argv[2]
    else:
        build_path = None  # Will use default (next to source repo)
    
    builder = ImageIPBuilder(source_path, build_path)
    success = builder.build_all()
    
    if success:
        print("\n🎯 Next steps:")
        print("1. Test the executable in the release folder")
        print("2. Go to https://github.com/ennisbl/ImageIP/releases")
        print("3. Create new release with tag v1.1.0")
        print("4. Upload the files from the release folder")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
