#!/usr/bin/env python3
"""
Build script for creating ResumeMindAI CLI executables
Supports Windows, macOS, and Linux
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def get_platform_info():
    """Get platform-specific information"""
    system = platform.system().lower()
    arch = platform.machine().lower()

    # Normalize architecture names
    if arch in ["x86_64", "amd64"]:
        arch = "x64"
    elif arch in ["aarch64", "arm64"]:
        arch = "arm64"
    elif arch in ["i386", "i686"]:
        arch = "x86"

    return system, arch


def clean_build_dirs():
    """Clean previous build directories"""
    dirs_to_clean = ["build", "dist", "__pycache__"]

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 Cleaning {dir_name}/")
            shutil.rmtree(dir_name)


def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
            text=True,
        )
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)


def build_executable():
    """Build the executable using PyInstaller"""
    system, arch = get_platform_info()

    print(f"🔨 Building executable for {system}-{arch}...")

    try:
        # Run PyInstaller with the spec file
        subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--clean",
                "--noconfirm",
                "resumemind_cli.spec",
            ],
            check=True,
        )

        print("✅ Executable built successfully!")

        # Get the executable path
        exe_name = "resumemind-cli"
        if system == "windows":
            exe_name += ".exe"

        exe_path = Path("dist") / exe_name

        if exe_path.exists():
            # Create release directory with platform info
            release_dir = Path("release") / f"{system}-{arch}"
            release_dir.mkdir(parents=True, exist_ok=True)

            # Copy executable to release directory
            release_exe = release_dir / exe_name
            shutil.copy2(exe_path, release_exe)

            # Copy additional files
            for file_name in ["README.md", "LICENSE", "docker-compose.yml"]:
                if Path(file_name).exists():
                    shutil.copy2(file_name, release_dir / file_name)

            print(f"📦 Release package created: {release_dir}")
            print(f"🎯 Executable location: {release_exe}")
            print(f"📏 File size: {release_exe.stat().st_size / (1024 * 1024):.1f} MB")

            return release_exe
        else:
            print(f"❌ Executable not found at {exe_path}")
            return None

    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return None


def create_installer_script(exe_path):
    """Create a simple installer script"""
    system, arch = get_platform_info()

    if system == "windows":
        # Create Windows batch installer
        installer_content = """@echo off
echo Installing ResumeMindAI CLI...
echo.

REM Create installation directory
set INSTALL_DIR=%USERPROFILE%\\ResumeMindAI
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy executable
copy "resumemind-cli.exe" "%INSTALL_DIR%\\"
copy "README.md" "%INSTALL_DIR%\\"
copy "LICENSE" "%INSTALL_DIR%\\"
copy "docker-compose.yml" "%INSTALL_DIR%\\"

REM Add to PATH (requires admin rights)
echo.
echo ResumeMindAI CLI installed to: %INSTALL_DIR%
echo.
echo To use from anywhere, add %INSTALL_DIR% to your PATH environment variable
echo or run: %INSTALL_DIR%\\resumemind-cli.exe
echo.
echo Installation complete!
pause
"""
        installer_path = exe_path.parent / "install.bat"

    else:
        # Create Unix shell installer
        installer_content = """#!/bin/bash
echo "Installing ResumeMindAI CLI..."
echo

# Create installation directory
INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

# Copy executable
cp resumemind-cli "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/resumemind-cli"

# Copy documentation
DOC_DIR="$HOME/.local/share/resumemind"
mkdir -p "$DOC_DIR"
cp README.md LICENSE docker-compose.yml "$DOC_DIR/" 2>/dev/null || true

echo
echo "ResumeMindAI CLI installed to: $INSTALL_DIR/resumemind-cli"
echo "Documentation copied to: $DOC_DIR"
echo

# Check if directory is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "⚠️  $INSTALL_DIR is not in your PATH"
    echo "Add this line to your ~/.bashrc or ~/.zshrc:"
    echo "export PATH=\\"$INSTALL_DIR:\$PATH\\""
    echo
fi

echo "✅ Installation complete!"
echo "Run 'resumemind-cli' to start the application"
"""
        installer_path = exe_path.parent / "install.sh"

    # Write installer script
    with open(installer_path, "w") as f:
        f.write(installer_content)

    # Make executable on Unix systems
    if system != "windows":
        os.chmod(installer_path, 0o755)

    print(f"📋 Installer script created: {installer_path}")


def main():
    """Main build process"""
    print("🚀 ResumeMindAI CLI - Executable Builder")
    print("=" * 50)

    system, arch = get_platform_info()
    print(f"🖥️  Platform: {system}-{arch}")
    print()

    # Step 1: Clean previous builds
    clean_build_dirs()

    # Step 2: Install dependencies
    install_dependencies()

    # Step 3: Build executable
    exe_path = build_executable()

    if exe_path:
        # Step 4: Create installer script
        create_installer_script(exe_path)

        print()
        print("🎉 Build completed successfully!")
        print(f"📦 Release package: {exe_path.parent}")
        print()
        print("Next steps:")
        print("1. Test the executable by running it")
        print("2. Share the release package with users")
        print("3. Users can run the installer script for easy setup")

    else:
        print("❌ Build failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
