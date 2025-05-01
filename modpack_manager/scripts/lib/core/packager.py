#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Packager for Minecraft Modpack Manager.
Handles creating client packs with mods and data packs.
Compatible with Python 2.7 and 3+.
"""

from __future__ import print_function, division, unicode_literals
import os
import sys
import json
import argparse
import tempfile
import shutil

# Add parent directory to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import config
from utils import logger
from utils import file_utils
from core.profile_manager import ProfileManager
from core.downloader import ModDownloader

# Python 2/3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    from io import open

class Packager:
    """
    Handles packaging modpacks for client distribution.
    """
    
    def __init__(self):
        """Initialize the packager."""
        self.profile_manager = ProfileManager()
        self.downloader = ModDownloader()
    
    def create_client_pack(self, profile_name):
        """
        Create a client pack for a modpack profile.
        
        Args:
            profile_name (str): Profile name
            
        Returns:
            str: Path to the client pack ZIP file if successful, None otherwise
        """
        # Load profile
        profile = self.profile_manager.load_profile(profile_name)
        if not profile:
            logger.error(f"Profile not found: {profile_name}")
            return None
        
        # Download mods and data packs if needed
        logger.info(f"Ensuring all content is downloaded for profile {profile_name}...")
        downloaded_files = self.downloader.download_profile_mods(profile)
        
        if not downloaded_files:
            logger.warning("No files downloaded or found in cache")
        
        # Create temporary directory for client pack
        temp_dir = tempfile.mkdtemp(prefix='modpack_')
        logger.debug(f"Created temp directory: {temp_dir}")
        
        try:
            # Create subdirectories
            mods_dir = os.path.join(temp_dir, 'mods')
            datapacks_dir = os.path.join(temp_dir, 'datapacks')
            
            file_utils.ensure_directory(mods_dir)
            file_utils.ensure_directory(datapacks_dir)
            
            # Copy mods
            mc_version = profile.get('minecraft_version')
            loader = profile.get('loader')
            
            # Get all mods (direct and dependencies)
            mods = profile.get('mods', []) + profile.get('dependencies', [])
            
            # Copy mod files
            for mod in mods:
                mod_id = mod.get('id')
                source = mod.get('source', '').lower()
                version = mod.get('version')
                
                if not mod_id or not source or not version:
                    logger.warning(f"Skipping invalid mod: {mod}")
                    continue
                
                # Find mod file in cache
                if source == 'modrinth':
                    mod_cache_dir = config.get_mod_cache_path(mc_version, loader)
                    # We don't know the exact filename, need to check contents of directory
                    if not os.path.exists(mod_cache_dir):
                        logger.warning(f"Mod cache directory not found: {mod_cache_dir}")
                        continue
                    
                    # Get download URL to extract filename
                    download_url = self.downloader.modrinth_api.get_version_download_url(version)
                    if not download_url:
                        logger.warning(f"Could not get download URL for mod {mod_id} version {version}")
                        continue
                    
                    filename = os.path.basename(download_url)
                    mod_path = os.path.join(mod_cache_dir, filename)
                    
                elif source == 'curseforge':
                    mod_cache_dir = config.get_mod_cache_path(mc_version, loader)
                    
                    # For CurseForge, we need to get file details
                    files = self.downloader.curseforge_api.get_mod_files(mod_id)
                    file_data = None
                    
                    for file in files:
                        if str(file.get('id')) == str(version):
                            file_data = file
                            break
                    
                    if not file_data:
                        logger.warning(f"Could not find file data for mod {mod_id} version {version}")
                        continue
                    
                    filename = file_data.get('fileName')
                    mod_path = os.path.join(mod_cache_dir, filename)
                
                # Copy mod file to client pack
                if os.path.exists(mod_path):
                    dest_path = os.path.join(mods_dir, filename)
                    file_utils.copy_file(mod_path, dest_path)
                    logger.debug(f"Copied mod: {filename}")
                else:
                    logger.warning(f"Mod file not found: {mod_path}")
            
            # Copy data packs
            datapacks = profile.get('datapacks', [])
            
            for datapack in datapacks:
                datapack_id = datapack.get('id')
                source = datapack.get('source', '').lower()
                version = datapack.get('version')
                
                if not datapack_id or not source or not version:
                    logger.warning(f"Skipping invalid data pack: {datapack}")
                    continue
                
                # Find data pack file in cache
                if source == 'modrinth':
                    datapack_cache_dir = config.get_datapack_cache_path(mc_version)
                    
                    # Get download URL to extract filename
                    download_url = self.downloader.modrinth_api.get_version_download_url(version)
                    if not download_url:
                        logger.warning(f"Could not get download URL for data pack {datapack_id} version {version}")
                        continue
                    
                    filename = os.path.basename(download_url)
                    datapack_path = os.path.join(datapack_cache_dir, filename)
                    
                elif source == 'curseforge':
                    datapack_cache_dir = config.get_datapack_cache_path(mc_version)
                    
                    # For CurseForge, we need to get file details
                    files = self.downloader.curseforge_api.get_mod_files(datapack_id)
                    file_data = None
                    
                    for file in files:
                        if str(file.get('id')) == str(version):
                            file_data = file
                            break
                    
                    if not file_data:
                        logger.warning(f"Could not find file data for data pack {datapack_id} version {version}")
                        continue
                    
                    filename = file_data.get('fileName')
                    datapack_path = os.path.join(datapack_cache_dir, filename)
                
                # Copy data pack file to client pack
                if os.path.exists(datapack_path):
                    dest_path = os.path.join(datapacks_dir, filename)
                    file_utils.copy_file(datapack_path, dest_path)
                    logger.debug(f"Copied data pack: {filename}")
                else:
                    logger.warning(f"Data pack file not found: {datapack_path}")
            
            # Create pack.json
            pack_info = {
                "name": profile.get('name'),
                "description": profile.get('description', ''),
                "version": "1.0.0",
                "minecraft_version": mc_version,
                "loader": loader,
                "loader_version": profile.get('loader_version'),
                "mods_count": len(mods),
                "datapacks_count": len(datapacks),
                "created": profile.get('updated')
            }
            
            file_utils.write_json(os.path.join(temp_dir, 'pack.json'), pack_info)
            
            # Create README.txt
            readme_content = f"""
{profile.get('name')} Modpack
{'-' * len(profile.get('name'))} -------

Description: {profile.get('description', '')}
Minecraft Version: {mc_version}
Loader: {loader.title()} {profile.get('loader_version')}
Mods: {len(mods)}
Data Packs: {len(datapacks)}

Installation Instructions:
1. Extract this ZIP file
2. Copy the 'mods' folder to your Minecraft instance directory
3. For data packs, copy the contents of the 'datapacks' folder to your world's 'datapacks' folder

Enjoy!
"""
            
            with open(os.path.join(temp_dir, 'README.txt'), 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            # Create ZIP file
            zip_path = config.get_client_pack_path(profile_name)
            if file_utils.create_zip(zip_path, temp_dir):
                logger.info(f"Created client pack: {zip_path}")
                return zip_path
            else:
                logger.error("Failed to create client pack ZIP file")
                return None
                
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir)
            logger.debug(f"Cleaned up temp directory: {temp_dir}")
        
        return None

def create_client_pack(args):
    """Command to create a client pack."""
    parser = argparse.ArgumentParser(description='Create a client pack for a modpack profile.')
    parser.add_argument('--profile', required=True, help='Profile name')
    
    try:
        parsed_args = parser.parse_args(args)
        
        packager = Packager()
        client_pack_path = packager.create_client_pack(parsed_args.profile)
        
        if client_pack_path:
            print(f"Client pack created: {client_pack_path}")
        else:
            print(f"Failed to create client pack for profile '{parsed_args.profile}'.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Test packaging functionality."""
    packager = Packager()
    
    print("Testing client pack creation...")
    
    # Create test profile if it doesn't exist
    profile_manager = ProfileManager()
    
    if not profile_manager.profile_exists("test_package"):
        print("Creating test profile...")
        profile = profile_manager.create_profile("test_package", "1.20.1", "fabric", "0.14.21")
        
        if profile:
            # Add mods
            profile_manager.add_mod("test_package", "create-fabric", "modrinth")
            
            # Add data packs
            profile_manager.add_datapack("test_package", "terralith", "modrinth")
    
    # Create client pack
    client_pack_path = packager.create_client_pack("test_package")
    
    if client_pack_path:
        print(f"Client pack created: {client_pack_path}")
    else:
        print("Failed to create client pack.")
    
if __name__ == '__main__':
    main() 