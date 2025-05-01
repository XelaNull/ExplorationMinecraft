#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File utilities for Minecraft Modpack Manager.
Handles file operations like creating and extracting ZIP files.
Compatible with Python 2.7 and 3+.
"""

from __future__ import print_function, division, unicode_literals
import os
import sys
import shutil
import zipfile
import json
import tempfile

# Add parent directory to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import config
from utils import logger

# Python 2/3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    from io import open

def ensure_directory(directory):
    """
    Ensure a directory exists.
    
    Args:
        directory (str): Directory path
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")
        return False

def copy_file(source, destination):
    """
    Copy a file from source to destination.
    
    Args:
        source (str): Source file path
        destination (str): Destination file path
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create destination directory if it doesn't exist
        dest_dir = os.path.dirname(destination)
        ensure_directory(dest_dir)
        
        # Copy the file
        shutil.copy2(source, destination)
        logger.debug(f"Copied {source} to {destination}")
        return True
    except Exception as e:
        logger.error(f"Error copying {source} to {destination}: {e}")
        return False

def delete_file(file_path):
    """
    Delete a file.
    
    Args:
        file_path (str): File path
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Deleted {file_path}")
            return True
        else:
            logger.warning(f"File does not exist: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Error deleting {file_path}: {e}")
        return False

def create_zip(zip_path, source_dir, include_dir=False):
    """
    Create a ZIP file from a directory.
    
    Args:
        zip_path (str): Path to the ZIP file to create
        source_dir (str): Source directory to compress
        include_dir (bool): Whether to include the directory name in the ZIP
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create parent directory if it doesn't exist
        zip_dir = os.path.dirname(zip_path)
        ensure_directory(zip_dir)
        
        # Create ZIP file
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Determine arcname (path within ZIP)
                    if include_dir:
                        arcname = os.path.relpath(file_path, os.path.dirname(source_dir))
                    else:
                        arcname = os.path.relpath(file_path, source_dir)
                    
                    zipf.write(file_path, arcname)
        
        logger.info(f"Created ZIP file: {zip_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating ZIP {zip_path}: {e}")
        return False

def extract_zip(zip_path, extract_dir):
    """
    Extract a ZIP file.
    
    Args:
        zip_path (str): Path to the ZIP file to extract
        extract_dir (str): Directory to extract to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create extract directory if it doesn't exist
        ensure_directory(extract_dir)
        
        # Extract ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            zipf.extractall(extract_dir)
        
        logger.info(f"Extracted ZIP file to: {extract_dir}")
        return True
    except Exception as e:
        logger.error(f"Error extracting ZIP {zip_path}: {e}")
        return False

def read_json(file_path):
    """
    Read a JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        dict: JSON data if successful, None otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSON {file_path}: {e}")
        return None

def write_json(file_path, data, indent=2):
    """
    Write data to a JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        data: Data to write
        indent (int): Indentation level
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create parent directory if it doesn't exist
        file_dir = os.path.dirname(file_path)
        ensure_directory(file_dir)
        
        # Write JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
        
        logger.debug(f"Wrote JSON file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing JSON {file_path}: {e}")
        return False

def create_client_pack(profile, mod_files):
    """
    Create a client pack ZIP file for a modpack profile.
    
    Args:
        profile (dict): Modpack profile data
        mod_files (list): List of mod file paths
        
    Returns:
        str: Path to the client pack ZIP file if successful, None otherwise
    """
    try:
        profile_name = profile.get('name')
        
        if not profile_name:
            logger.error("Profile missing name")
            return None
        
        # Create a temp directory for the client pack
        temp_dir = tempfile.mkdtemp(prefix='modpack_')
        logger.debug(f"Created temp directory: {temp_dir}")
        
        # Create subdirectories
        mods_dir = os.path.join(temp_dir, 'mods')
        ensure_directory(mods_dir)
        
        # Copy mods
        for mod_file in mod_files:
            mod_name = os.path.basename(mod_file)
            dest_path = os.path.join(mods_dir, mod_name)
            copy_file(mod_file, dest_path)
        
        # Create pack info file
        pack_info = {
            "name": profile.get('name'),
            "description": profile.get('description', ''),
            "minecraft_version": profile.get('minecraft_version'),
            "loader": profile.get('loader'),
            "loader_version": profile.get('loader_version'),
            "mods_count": len(mod_files)
        }
        
        write_json(os.path.join(temp_dir, 'pack.json'), pack_info)
        
        # Create ZIP file
        zip_path = config.get_client_pack_path(profile_name)
        create_zip(zip_path, temp_dir)
        
        # Clean up temp directory
        shutil.rmtree(temp_dir)
        
        logger.info(f"Created client pack: {zip_path}")
        return zip_path
    except Exception as e:
        logger.error(f"Error creating client pack: {e}")
        return None

def extract_mrpack(mrpack_path, extract_dir):
    """
    Extract an mrpack (Modrinth modpack) file.
    
    Args:
        mrpack_path (str): Path to the mrpack file
        extract_dir (str): Directory to extract to
        
    Returns:
        dict: Modpack metadata if successful, None otherwise
    """
    try:
        # mrpack files are ZIP files
        return extract_zip(mrpack_path, extract_dir)
    except Exception as e:
        logger.error(f"Error extracting mrpack {mrpack_path}: {e}")
        return None

def main():
    """Test file utility functionality."""
    # Test directory creation
    test_dir = os.path.join(config.PROJECT_ROOT, 'test_dir')
    print(f"Creating directory: {test_dir}")
    ensure_directory(test_dir)
    
    # Test JSON operations
    test_json = os.path.join(test_dir, 'test.json')
    test_data = {
        "name": "Test Data",
        "description": "This is test data",
        "values": [1, 2, 3, 4, 5]
    }
    
    print(f"Writing JSON: {test_json}")
    write_json(test_json, test_data)
    
    print(f"Reading JSON: {test_json}")
    read_data = read_json(test_json)
    print(f"Read data: {read_data}")
    
    # Test ZIP operations
    test_zip = os.path.join(test_dir, 'test.zip')
    print(f"Creating ZIP: {test_zip}")
    create_zip(test_zip, test_dir)
    
    test_extract_dir = os.path.join(test_dir, 'extract')
    print(f"Extracting ZIP to: {test_extract_dir}")
    extract_zip(test_zip, test_extract_dir)
    
    # Clean up
    print("Cleaning up test files")
    shutil.rmtree(test_dir)
    
if __name__ == '__main__':
    main() 