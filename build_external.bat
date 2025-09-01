@echo off
title ImageIP External Build System
echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                ImageIP External Build System              ║
echo ║           Keeps your repository clean and organized       ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

echo 🏗️ This will create a clean build workspace outside your repo
echo 📁 Source: %~dp0
echo 🔧 Build:  %~dp0..\ImageIP-Build
echo.

pause

echo 🚀 Starting external build process...
echo.

python "%~dp0external_builder.py" "%~dp0"

if errorlevel 1 (
    echo.
    echo ❌ Build failed! Check the output above for errors.
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ External build completed successfully!
echo.
echo 📁 Your repository remains clean
echo 🗂️ Release files are in: %~dp0..\ImageIP-Build\releases\
echo.
echo Ready to upload to GitHub! 🚀
echo.
pause
