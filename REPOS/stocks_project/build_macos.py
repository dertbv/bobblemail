#!/usr/bin/env python3
"""
macOS Build Script for Stocks Analyzer
Automates the entire build process from source to DMG installer
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import tempfile
import argparse
import json
from PIL import Image, ImageDraw
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StocksBuildSystem:
    """Complete build system for macOS packaging"""
    
    def __init__(self, source_dir=None, clean=False):
        self.source_dir = Path(source_dir or os.getcwd())
        self.clean = clean
        self.build_dir = self.source_dir / 'build'
        self.dist_dir = self.source_dir / 'dist'
        self.assets_dir = self.source_dir / 'assets'
        
        # Build info
        self.app_name = 'StocksAnalyzer'
        self.app_version = '1.0.0'
        self.bundle_id = 'com.stocksanalyzer.app'
        
        logger.info(f"Building from: {self.source_dir}")
    
    def clean_build(self):
        """Clean previous build artifacts"""
        logger.info("Cleaning previous builds...")
        
        dirs_to_clean = [self.build_dir, self.dist_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                logger.info(f"Removed {dir_path}")
        
        # Remove pyinstaller cache
        cache_dirs = [
            self.source_dir / '__pycache__',
            Path.home() / '.pyinstaller_cache'
        ]
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                logger.info(f"Removed cache {cache_dir}")
    
    def check_dependencies(self):
        """Check if all required tools are available"""
        logger.info("Checking build dependencies...")
        
        required_tools = ['pyinstaller', 'pip']
        missing_tools = []
        
        for tool in required_tools:
            try:
                subprocess.run([tool, '--version'], 
                             capture_output=True, check=True)
                logger.info(f"✓ {tool} is available")
            except (subprocess.SubprocessError, FileNotFoundError):
                missing_tools.append(tool)
                logger.error(f"✗ {tool} is missing")
        
        if missing_tools:
            logger.error(f"Missing required tools: {', '.join(missing_tools)}")
            logger.info("Install missing tools with:")
            logger.info("pip install pyinstaller pillow")
            return False
        
        return True
    
    def create_assets(self):
        """Create application icon and other assets"""
        logger.info("Creating application assets...")
        
        self.assets_dir.mkdir(exist_ok=True)
        
        # Create a simple icon
        icon_path = self.assets_dir / 'icon.icns'
        if not icon_path.exists():
            self.create_app_icon(icon_path)
        
        return True
    
    def create_app_icon(self, icon_path):
        """Create a simple application icon"""
        logger.info("Creating application icon...")
        
        # Create icon at multiple sizes
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        images = []
        
        for size in sizes:
            # Create a simple icon with stock chart-like appearance
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Background circle
            margin = size // 8
            draw.ellipse([margin, margin, size-margin, size-margin], 
                        fill=(0, 122, 255, 255))  # Apple blue
            
            # Simple chart line
            line_points = [
                (size * 0.2, size * 0.7),
                (size * 0.4, size * 0.5),
                (size * 0.6, size * 0.3),
                (size * 0.8, size * 0.4)
            ]
            
            # Draw connecting lines
            for i in range(len(line_points) - 1):
                draw.line([line_points[i], line_points[i+1]], 
                         fill=(255, 255, 255, 255), width=max(1, size//32))
            
            # Draw points
            point_size = max(2, size // 64)
            for point in line_points:
                draw.ellipse([point[0]-point_size, point[1]-point_size, 
                            point[0]+point_size, point[1]+point_size], 
                           fill=(255, 255, 255, 255))
            
            images.append(img)
        
        # Save as .icns for macOS
        try:
            # Save the largest image as PNG first
            png_path = icon_path.with_suffix('.png')
            images[-1].save(png_path, 'PNG')
            
            # Convert to .icns using macOS tools
            subprocess.run(['sips', '-s', 'format', 'icns', 
                          str(png_path), '--out', str(icon_path)], 
                         check=True, capture_output=True)
            
            # Clean up PNG
            png_path.unlink()
            logger.info(f"Created icon: {icon_path}")
            
        except subprocess.SubprocessError:
            # Fallback: save as PNG and rename
            logger.warning("Could not create .icns, using PNG fallback")
            images[-1].save(icon_path.with_suffix('.png'), 'PNG')
    
    def install_dependencies(self):
        """Install Python dependencies"""
        logger.info("Installing Python dependencies...")
        
        # Check if requirements.txt exists
        req_file = self.source_dir / 'requirements.txt'
        if not req_file.exists():
            logger.error("requirements.txt not found")
            return False
        
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', 
                '-r', str(req_file)
            ], check=True)
            
            # Install build dependencies
            subprocess.run([
                sys.executable, '-m', 'pip', 'install',
                'pyinstaller', 'pillow'
            ], check=True)
            
            logger.info("Dependencies installed successfully")
            return True
            
        except subprocess.SubprocessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def build_executable(self):
        """Build the executable using PyInstaller"""
        logger.info("Building executable with PyInstaller...")
        
        spec_file = self.source_dir / 'stocks.spec'
        if not spec_file.exists():
            logger.error("stocks.spec file not found")
            return False
        
        try:
            # Run PyInstaller
            cmd = [
                'pyinstaller',
                '--clean',
                '--noconfirm',
                str(spec_file)
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=str(self.source_dir), 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"PyInstaller failed: {result.stderr}")
                return False
            
            # Check if app was created
            app_path = self.dist_dir / f'{self.app_name}.app'
            if not app_path.exists():
                logger.error(f"Application bundle not found at {app_path}")
                return False
            
            logger.info(f"✓ Application built: {app_path}")
            return True
            
        except Exception as e:
            logger.error(f"Build failed: {e}")
            return False
    
    def create_dmg(self):
        """Create a DMG installer package"""
        logger.info("Creating DMG installer...")
        
        app_path = self.dist_dir / f'{self.app_name}.app'
        if not app_path.exists():
            logger.error("App bundle not found, cannot create DMG")
            return False
        
        dmg_path = self.dist_dir / f'{self.app_name}-{self.app_version}.dmg'
        temp_dmg_dir = self.build_dir / 'dmg_contents'
        
        try:
            # Create temporary directory for DMG contents
            if temp_dmg_dir.exists():
                shutil.rmtree(temp_dmg_dir)
            temp_dmg_dir.mkdir(parents=True)
            
            # Copy app to DMG directory
            shutil.copytree(app_path, temp_dmg_dir / f'{self.app_name}.app')
            
            # Create Applications symlink
            os.symlink('/Applications', temp_dmg_dir / 'Applications')
            
            # Create DMG
            subprocess.run([
                'hdiutil', 'create',
                '-volname', self.app_name,
                '-srcfolder', str(temp_dmg_dir),
                '-ov',
                '-format', 'UDZO',
                str(dmg_path)
            ], check=True)
            
            logger.info(f"✓ DMG created: {dmg_path}")
            return True
            
        except subprocess.SubprocessError as e:
            logger.error(f"DMG creation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating DMG: {e}")
            return False
    
    def create_build_info(self):
        """Create build information file"""
        build_info = {
            'app_name': self.app_name,
            'version': self.app_version,
            'bundle_id': self.bundle_id,
            'build_date': subprocess.check_output(['date']).decode().strip(),
            'build_machine': subprocess.check_output(['hostname']).decode().strip(),
            'python_version': sys.version,
            'pyinstaller_version': subprocess.check_output(['pyinstaller', '--version']).decode().strip()
        }
        
        info_file = self.dist_dir / 'build_info.json'
        with open(info_file, 'w') as f:
            json.dump(build_info, f, indent=2)
        
        logger.info(f"Build info saved to: {info_file}")
    
    def run_tests(self):
        """Run basic tests on the built application"""
        logger.info("Running post-build tests...")
        
        app_path = self.dist_dir / f'{self.app_name}.app'
        if not app_path.exists():
            logger.error("App not found for testing")
            return False
        
        # Test 1: Check app bundle structure
        required_paths = [
            app_path / 'Contents',
            app_path / 'Contents' / 'MacOS',
            app_path / 'Contents' / 'Resources',
            app_path / 'Contents' / 'Info.plist'
        ]
        
        for path in required_paths:
            if not path.exists():
                logger.error(f"Missing required path: {path}")
                return False
        
        logger.info("✓ App bundle structure is valid")
        
        # Test 2: Check if executable exists and is executable
        exe_path = app_path / 'Contents' / 'MacOS' / 'stocks_launcher'
        if not exe_path.exists():
            logger.error("Main executable not found")
            return False
        
        if not os.access(exe_path, os.X_OK):
            logger.error("Main executable is not executable")
            return False
        
        logger.info("✓ Executable is present and executable")
        
        logger.info("✓ All tests passed")
        return True
    
    def build(self):
        """Run the complete build process"""
        logger.info(f"Starting build for {self.app_name} v{self.app_version}")
        
        try:
            # Step 1: Clean previous builds if requested
            if self.clean:
                self.clean_build()
            
            # Step 2: Check dependencies
            if not self.check_dependencies():
                return False
            
            # Step 3: Install Python dependencies
            if not self.install_dependencies():
                return False
            
            # Step 4: Create assets
            if not self.create_assets():
                return False
            
            # Step 5: Build executable
            if not self.build_executable():
                return False
            
            # Step 6: Run tests
            if not self.run_tests():
                return False
            
            # Step 7: Create DMG
            if not self.create_dmg():
                return False
            
            # Step 8: Create build info
            self.create_build_info()
            
            logger.info("🎉 Build completed successfully!")
            logger.info(f"App bundle: {self.dist_dir / f'{self.app_name}.app'}")
            logger.info(f"DMG installer: {self.dist_dir / f'{self.app_name}-{self.app_version}.dmg'}")
            
            return True
            
        except Exception as e:
            logger.error(f"Build failed with error: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Build Stocks Analyzer for macOS')
    parser.add_argument('--clean', action='store_true', 
                       help='Clean previous builds before building')
    parser.add_argument('--source-dir', type=str, 
                       help='Source directory (default: current directory)')
    
    args = parser.parse_args()
    
    # Create build system
    builder = StocksBuildSystem(
        source_dir=args.source_dir,
        clean=args.clean
    )
    
    # Run build
    success = builder.build()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()