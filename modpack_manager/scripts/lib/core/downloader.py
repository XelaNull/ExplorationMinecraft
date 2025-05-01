#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mod downloader for Minecraft Modpack Manager.
Handles downloading mods from Modrinth and CurseForge.
Compatible with Python 2.7 and 3+.
"""

from __future__ import print_function, division, unicode_literals
import os
import sys
import hashlib
import shutil
import time

# Add parent directory to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import config
from api.modrinth import ModrinthAPI
from api.curseforge import CurseForgeAPI

# Python 2/3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    from io import open
    from urllib2 import Request, urlopen, URLError, HTTPError
else:
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError

class ModDownloader:
    """
    Handles downloading mods from various sources.
    """
    
    def __init__(self):
        """Initialize API clients."""
        self.modrinth_api = ModrinthAPI()
        self.curseforge_api = CurseForgeAPI()
    
    def _calculate_file_hash(self, file_path, hash_type='sha1'):
        """
        Calculate hash for a file.
        
        Args:
            file_path (str): Path to the file
            hash_type (str): Hash algorithm to use (md5, sha1, sha256)
            
        Returns:
            str: Hex digest of the hash
        """
        if hash_type == 'md5':
            hash_func = hashlib.md5()
        elif hash_type == 'sha1':
            hash_func = hashlib.sha1()
        elif hash_type == 'sha256':
            hash_func = hashlib.sha256()
        else:
            raise ValueError(f"Unsupported hash type: {hash_type}")
        
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def _download_file(self, url, output_path):
        """
        Download a file from a URL.
        
        Args:
            url (str): URL to download from
            output_path (str): Path to save the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Create parent directories if they don't exist
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Set up temporary file path
        temp_path = output_path + '.download'
        
        # Set up request
        headers = {
            'User-Agent': config.USER_AGENT
        }
        req = Request(url, headers=headers)
        
        try:
            # Open the URL
            response = urlopen(req)
            
            # Open the output file
            with open(temp_path, 'wb') as f:
                # Get the total file size if possible
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 8192
                
                # Download in chunks
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Print progress
                    if total_size > 0:
                        percent = int(downloaded * 100 / total_size)
                        sys.stdout.write(f"\rDownloading: {percent}% ({downloaded}/{total_size} bytes)")
                        sys.stdout.flush()
            
            # Move the downloaded file to the final location
            shutil.move(temp_path, output_path)
            print(f"\nDownload complete: {output_path}")
            return True
            
        except HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
            
        except URLError as e:
            print(f"URL Error: {e.reason}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
    
    def download_from_modrinth(self, mod_id, version_id, mc_version, loader=None, content_type='mod'):
        """
        Download a mod or data pack from Modrinth.
        
        Args:
            mod_id (str): Mod ID (slug or project ID)
            version_id (str): Version ID
            mc_version (str): Minecraft version
            loader (str, optional): Mod loader (fabric, forge)
            content_type (str): Type of content ('mod' or 'datapack')
            
        Returns:
            tuple: (file_path, version_id) where:
                - file_path (str or None): Path to downloaded file if successful, None otherwise
                - version_id (str): The version ID that was actually used (may differ from input if fallback occurred)
        """
        from api.modrinth import ModrinthAPI
        
        # Setup cache directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        cache_dir = os.path.join(project_root, 'modpack_cache', mc_version, loader if loader else 'datapacks')
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize API
        api = ModrinthAPI()
        
        # Get the download URL
        download_url = api.get_version_download_url(version_id)
        
        # If version_id not found, try to find the latest compatible version
        if not download_url:
            print(f"Version ID {version_id} not found, searching for latest compatible version...")
            
            # Get mod details and versions
            mod_details = api.get_mod(mod_id)
            if not mod_details:
                print(f"Error: Could not find mod with ID {mod_id}")
                return None, version_id
                
            versions = api.get_mod_versions(mod_id, minecraft_version=mc_version, loader=loader)
            if not versions:
                print(f"Error: No compatible versions found for {mod_details.get('title', mod_id)}")
                return None, version_id
                
            # Verify the version is compatible with our loader
            valid_versions = []
            loader_lower = loader.lower() if loader else "unknown"
            
            # For Forge mods, be stricter about which versions to accept
            for version in versions:
                version_loaders = version.get('loaders', [])
                if loader_lower == 'forge':
                    # For forge mods, only accept pure forge mods (not neoforge or fabric)
                    if len(version_loaders) == 1 and loader_lower in version_loaders:
                        valid_versions.append(version)
                else:
                    # For other loaders, just make sure our loader is included
                    if loader_lower in version_loaders:
                        valid_versions.append(version)
            
            if not valid_versions:
                print(f"Error: No versions specifically for {loader} found")
                print(f"Available loaders for this mod: {[v.get('loaders') for v in versions[:3]]}")
                return None, version_id
            
            # Get the latest compatible version
            latest_version = valid_versions[0]  # Already sorted newest first
            version_id = latest_version.get('id')
            
            print(f"Found new compatible version: {latest_version.get('name')} ({version_id})")
            print(f"Loader compatibility: {latest_version.get('loaders')}")
            download_url = api.get_version_download_url(version_id)
            
            if not download_url:
                print(f"Error: Could not get download URL for version {version_id}")
                return None, version_id
                
            print(f"Download URL: {download_url}")
        
        # Get the file name from the URL
        file_name = os.path.basename(download_url).split('?')[0]
        
        # Add mod/version ID as prefix if filename is generic
        if file_name in ['download', 'file', 'mod.jar', 'datapack.zip']:
            file_name = f"{mod_id}_{version_id}_{file_name}"
        
        # Ensure the correct extension
        if content_type == 'mod' and not file_name.endswith('.jar'):
            file_name += '.jar'
        elif content_type == 'datapack' and not file_name.endswith('.zip'):
            file_name += '.zip'
        
        # Set the output path
        output_path = os.path.join(cache_dir, file_name)
        
        # Check if the file already exists
        if os.path.exists(output_path):
            print(f"File already exists: {output_path}")
            return output_path, version_id
        
        # Download the file
        if self._download_file(download_url, output_path):
            return output_path, version_id
        
        return None, version_id
    
    def download_from_curseforge(self, mod_id, file_id, mc_version, loader=None, content_type='mod'):
        """
        Download a mod or data pack from CurseForge.
        
        Args:
            mod_id (int): Mod ID
            file_id (int): File ID
            mc_version (str): Minecraft version
            loader (str, optional): Mod loader (fabric, forge) - not needed for datapacks
            content_type (str, optional): Type of content to download ('mod' or 'datapack')
            
        Returns:
            tuple: (file_path, version_id) where:
                - file_path (str or None): Path to downloaded file if successful, None otherwise
                - version_id (str or int): The file ID that was used
        """
        # Get the mod details to determine the file name
        mod = self.curseforge_api.get_mod(mod_id)
        print(f"DEBUG: Curseforge get_mod returned: {mod}")
        
        if not mod:
            print(f"Error: {content_type.title()} {mod_id} not found")
            return None, file_id
        
        # Print mod details for debugging
        print(f"Mod details for {mod_id}:")
        print(f"  Name: {mod.get('name', 'Unknown')}")
        print(f"  Summary: {mod.get('summary', 'Unknown')}")
        print(f"  Slug: {mod.get('slug', 'Unknown')}")
        
        # Get the file details - try with loader filter first
        files = self.curseforge_api.get_mod_files(mod_id, mc_version, loader)
        file_data = None
        
        # If not found, try without the loader filter
        if not files or len(files) == 0:
            print(f"No files found with loader={loader}, trying without loader filter")
            files = self.curseforge_api.get_mod_files(mod_id, mc_version)
        
        # If still not found, try without any filters
        if not files or len(files) == 0:
            print(f"No files found with mc_version={mc_version}, trying without any filters")
            files = self.curseforge_api.get_mod_files(mod_id)
        
        if files:
            print(f"Found {len(files)} files for mod {mod_id}")
            # First try to find the specific file ID
            for file in files:
                if file.get('id') == file_id:
                    file_data = file
                    print(f"Found matching file: {file.get('displayName', 'Unknown')}")
                    break
        
        if not file_data:
            print(f"Error: File {file_id} not found for {content_type} {mod_id}")
            return None, file_id
        
        # For debugging, print file_data
        if file_data:
            print(f"File data details:")
            print(f"  File name: {file_data.get('fileName', 'Unknown')}")
            print(f"  File ID: {file_data.get('id', 'Unknown')}")
            game_versions = file_data.get('gameVersions', [])
            print(f"  Game versions: {', '.join(game_versions) if game_versions else 'Unknown'}")
            print(f"  Download URL from file_data: {file_data.get('downloadUrl', 'Not available')}")
        
        # Try to use downloadUrl directly from file_data first (some CurseForge responses include it)
        direct_download_url = file_data.get('downloadUrl')
        if direct_download_url:
            print(f"Using direct download URL from file data: {direct_download_url}")
            download_url = direct_download_url
        else:
            # Get the download URL from API
            download_url = self.curseforge_api.get_download_url(mod_id, file_id)
            print(f"Attempting to download from URL: {download_url}")
        
        if not download_url:
            print(f"Error: Download URL for {mod_id} file {file_id} not found")
            return None, file_id
        
        # Create the cache directory
        if content_type == 'mod':
            cache_dir = config.get_cache_dir(mc_version, loader.lower())
        else:  # datapack
            cache_dir = config.get_datapack_cache_path(mc_version)
        
        # Get the file name
        file_name = file_data.get('fileName', f"{mod_id}_{file_id}.jar")
        
        # Set the output path
        output_path = os.path.join(cache_dir, file_name)
        
        # Check if the file already exists
        if os.path.exists(output_path):
            print(f"File already exists: {output_path}")
            return output_path, file_id
        
        # Download the file
        print(f"Starting download of file {file_name} to {output_path}")
        download_success = self._download_file(download_url, output_path)
        
        if download_success:
            print(f"Successfully downloaded file to {output_path}")
            return output_path, file_id
        else:
            print(f"Failed to download file from {download_url}")
            return None, file_id
        
        return None, file_id
    
    def download_mod(self, mod, mc_version, loader):
        """
        Download a mod from the appropriate source.
        
        Args:
            mod (dict): Mod data with source, id, and version information
            mc_version (str): Minecraft version
            loader (str): Mod loader (fabric, forge)
            
        Returns:
            tuple: (file_path, version_id) where:
                - file_path (str or None): Path to downloaded file if successful, None otherwise
                - version_id (str): The version ID that was actually used (may differ from input if fallback occurred)
        """
        source = mod.get('source', '').lower()
        mod_id = mod.get('id')
        version_id = mod.get('version')
        
        if not mod_id:
            print(f"Error: Invalid mod data: {mod}")
            return None, version_id
        
        print(f"Downloading mod from {source}: {mod_id} (version: {version_id})")
        
        if source == 'modrinth':
            file_path, version_id = self.download_from_modrinth(mod_id, version_id, mc_version, loader, 'mod')
            return file_path, version_id
        elif source == 'curseforge':
            # Handle 'latest' version for CurseForge
            if version_id == 'latest':
                print(f"Finding latest version for mod {mod_id} on CurseForge...")
                # Get mod files to find the latest compatible file
                files = self.curseforge_api.get_mod_files(mod_id, mc_version, loader)
                
                if not files or len(files) == 0:
                    print(f"Error: No files found for mod {mod_id} on CurseForge with loader filter")
                    
                    # Try without loader filter as fallback
                    print(f"Trying again without loader filter...")
                    files = self.curseforge_api.get_mod_files(mod_id, mc_version)
                    
                    if not files or len(files) == 0:
                        print(f"Error: Still no files found for mod {mod_id} on CurseForge")
                        return None, version_id
                    
                # Print some debug info
                print(f"Found {len(files)} files for mod {mod_id}")
                for idx, file in enumerate(files[:3]):  # Show top 3 files
                    print(f"  File {idx+1}: {file.get('displayName', 'Unknown')} (ID: {file.get('id')})")
                
                # Get the first file (latest by default since the API sorts by date)
                latest_file = files[0]
                file_id = latest_file.get('id')
                
                if file_id:
                    print(f"Selected latest version: {latest_file.get('displayName', 'Unknown')} (ID: {file_id})")
                    version_id = str(file_id)
                else:
                    print(f"Error: Could not determine file ID for latest version of {mod_id}")
                    return None, version_id
            
            try:
                # Convert version_id to integer for CurseForge
                int_version_id = int(version_id)
                file_path, version_id = self.download_from_curseforge(mod_id, int_version_id, mc_version, loader, 'mod')
                return file_path, version_id
            except ValueError as e:
                print(f"Error: Invalid version ID for CurseForge: {version_id} - {e}")
                return None, version_id
        else:
            print(f"Error: Unsupported mod source: {source}")
            return None, version_id
    
    def download_datapack(self, datapack, mc_version):
        """
        Download a data pack from the appropriate source.
        
        Args:
            datapack (dict): Data pack data with source, id, and version information
            mc_version (str): Minecraft version
            
        Returns:
            tuple: (file_path, version_id) where:
                - file_path (str or None): Path to downloaded file if successful, None otherwise
                - version_id (str): The version ID that was actually used
        """
        source = datapack.get('source', '').lower()
        datapack_id = datapack.get('id')
        version_id = datapack.get('version')
        
        if not datapack_id or not version_id:
            print(f"Error: Invalid data pack data: {datapack}")
            return None, version_id
        
        if source == 'modrinth':
            file_path, version_id = self.download_from_modrinth(datapack_id, version_id, mc_version, None, 'datapack')
            return file_path, version_id
        elif source == 'curseforge':
            file_path, version_id = self.download_from_curseforge(datapack_id, int(version_id), mc_version, None, 'datapack')
            return file_path, version_id
        else:
            print(f"Error: Unsupported data pack source: {source}")
            return None, version_id
    
    def download_profile_mods(self, profile):
        """
        Download all mods for a profile.
        
        Args:
            profile (dict): Profile data with mods list
            
        Returns:
            list: List of paths to downloaded files
        """
        if not profile:
            print("Error: Invalid profile")
            return []
        
        mc_version = profile.get('minecraft_version')
        loader = profile.get('loader')
        mods = profile.get('mods', [])
        dependencies = profile.get('dependencies', [])
        datapacks = profile.get('datapacks', [])
        
        if not mc_version or not loader:
            print("Error: Profile missing required fields")
            return []
        
        # Combine mods and dependencies
        all_mods = mods + dependencies
        
        if not all_mods and not datapacks:
            print("No content to download")
            return []
        
        downloaded_files = []
        
        # Download mods and dependencies
        if all_mods:
            print(f"Downloading {len(all_mods)} mods for profile {profile.get('name')}")
            
            for i, mod in enumerate(all_mods):
                print(f"\nDownloading mod {i+1}/{len(all_mods)}: {mod.get('name')}")
                file_path, version_id = self.download_mod(mod, mc_version, loader)
                
                if file_path:
                    downloaded_files.append((file_path, version_id))
            
            print(f"\nDownloaded {len(downloaded_files)}/{len(all_mods)} mods")
        
        # Download data packs
        if datapacks:
            print(f"\nDownloading {len(datapacks)} data packs for profile {profile.get('name')}")
            
            datapack_count = 0
            for i, datapack in enumerate(datapacks):
                print(f"\nDownloading data pack {i+1}/{len(datapacks)}: {datapack.get('name')}")
                file_path, version_id = self.download_datapack(datapack, mc_version)
                
                if file_path:
                    downloaded_files.append((file_path, version_id))
                    datapack_count += 1
            
            print(f"\nDownloaded {datapack_count}/{len(datapacks)} data packs")
        
        return downloaded_files

def download_profile(args):
    """Command to download all mods for a profile."""
    import argparse
    from core.profile_manager import ProfileManager
    
    parser = argparse.ArgumentParser(description='Download all mods for a profile.')
    parser.add_argument('--profile', required=True, help='Profile name')
    
    try:
        parsed_args = parser.parse_args(args)
        
        # Load profile
        profile_manager = ProfileManager()
        profile = profile_manager.load_profile(parsed_args.profile)
        
        if not profile:
            print(f"Profile '{parsed_args.profile}' not found.")
            return
        
        # Download mods
        downloader = ModDownloader()
        downloaded_files = downloader.download_profile_mods(profile)
        
        print(f"\nDownloaded {len(downloaded_files)} files for profile '{parsed_args.profile}'.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Test mod downloading functionality."""
    from profile_manager import load_profile
    
    downloader = ModDownloader()
    
    # Test downloading a specific mod
    print("Testing mod download...")
    
    # Example profile creation
    profile = {
        "name": "test_profile",
        "minecraft_version": "1.20.1",
        "loader": "fabric",
        "mods": [
            {
                "name": "Create",
                "id": "create-fabric",
                "version": "0.5.1-d",
                "source": "modrinth"
            }
        ],
        "datapacks": [
            {
                "name": "Terralith",
                "id": "terralith",
                "version": "2.4.0",
                "source": "modrinth"
            }
        ]
    }
    
    # Download mods for the profile
    downloader.download_profile_mods(profile)
    
if __name__ == '__main__':
    main() 