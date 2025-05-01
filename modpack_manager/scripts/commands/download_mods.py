#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Download all mods for a modpack profile.
Handles client-side and server-side mods separately.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from lib.core.profile_manager import ProfileManager
from lib.core.downloader import ModDownloader
from lib.core.mod_search import ModSearch
from utils import config

def main():
    """Handle downloading mods for a profile."""
    parser = argparse.ArgumentParser(description='Download all mods for a profile.')
    parser.add_argument('--profile', required=True, help='Profile name')
    parser.add_argument('--client-only', action='store_true', help='Download only client-side mods')
    parser.add_argument('--server-only', action='store_true', help='Download only server-side mods')
    parser.add_argument('--force', action='store_true', help='Force re-download even if mod exists in cache')
    parser.add_argument('--update-versions', action='store_true', help='Update profile with latest compatible versions')
    
    args = parser.parse_args()
    
    profile_manager = ProfileManager()
    profile = profile_manager.load_profile(args.profile)
    
    if not profile:
        print(f"Profile '{args.profile}' not found.")
        sys.exit(1)
    
    print(f"Downloading mods for profile '{args.profile}'")
    print(f"Minecraft: {profile.get('minecraft_version')}")
    print(f"Loader: {profile.get('loader')} {profile.get('loader_version')}")
    
    # Set up downloader and search
    downloader = ModDownloader()
    mod_search = ModSearch()
    
    # Determine which mods to download based on side
    all_mods = []
    client_only_mods = []
    server_only_mods = []
    both_sides_mods = []
    dependencies = []
    profile_updated = False
    
    # Process mods based on side
    for mod in profile.get('mods', []):
        side = mod.get('side', 'both').lower()
        
        if side == 'client':
            client_only_mods.append(mod)
        elif side == 'server':
            server_only_mods.append(mod)
        else:
            both_sides_mods.append(mod)
    
    # Process dependencies
    for dep in profile.get('dependencies', []):
        dependencies.append(dep)
    
    # Determine which mods to download based on command line arguments
    if args.client_only:
        all_mods = client_only_mods + both_sides_mods + dependencies
        print(f"Downloading {len(all_mods)} mods for client")
    elif args.server_only:
        all_mods = server_only_mods + both_sides_mods + dependencies
        print(f"Downloading {len(all_mods)} mods for server")
    else:
        all_mods = client_only_mods + server_only_mods + both_sides_mods + dependencies
        print(f"Downloading {len(all_mods)} mods for both client and server")
    
    # Download mods
    minecraft_version = profile.get('minecraft_version')
    loader = profile.get('loader')
    
    mod_files = []
    for i, mod in enumerate(all_mods):
        print(f"\nDownloading mod {i+1}/{len(all_mods)}: {mod.get('name')} ({mod.get('source')})")
        file_path = downloader.download_mod(mod, minecraft_version, loader)
        
        # If download failed and source is Modrinth, try to get the latest compatible version
        if not file_path and mod.get('source').lower() == 'modrinth':
            print(f"Trying to find latest compatible version for {mod.get('name')}...")
            mod_id = mod.get('id')
            versions = mod_search.modrinth_api.get_mod_versions(mod_id, minecraft_version, loader)
            
            if versions:
                # Get the latest version
                latest_version = versions[0]
                latest_version_id = latest_version.get('id')
                print(f"Found new version: {latest_version.get('name')} (ID: {latest_version_id})")
                
                # Update mod entry in profile with new version ID
                mod['version'] = latest_version_id
                profile_updated = True
                
                # Try downloading with new version ID
                file_path = downloader.download_mod(mod, minecraft_version, loader)
        
        if file_path:
            mod_files.append(file_path)
    
    # Download data packs if needed
    datapacks = profile.get('datapacks', [])
    if datapacks:
        print(f"\nDownloading {len(datapacks)} data packs")
        for i, datapack in enumerate(datapacks):
            print(f"\nDownloading data pack {i+1}/{len(datapacks)}: {datapack.get('name')} ({datapack.get('source')})")
            file_path = downloader.download_datapack(datapack, minecraft_version)
            
            # If download failed and source is Modrinth, try to get the latest compatible version
            if not file_path and datapack.get('source').lower() == 'modrinth':
                print(f"Trying to find latest compatible version for {datapack.get('name')}...")
                datapack_id = datapack.get('id')
                versions = mod_search.modrinth_api.get_mod_versions(datapack_id, minecraft_version)
                
                if versions:
                    # Get the latest version
                    latest_version = versions[0]
                    latest_version_id = latest_version.get('id')
                    print(f"Found new version: {latest_version.get('name')} (ID: {latest_version_id})")
                    
                    # Update datapack entry in profile with new version ID
                    datapack['version'] = latest_version_id
                    profile_updated = True
                    
                    # Try downloading with new version ID
                    file_path = downloader.download_datapack(datapack, minecraft_version)
            
            if file_path:
                mod_files.append(file_path)
    
    print(f"\nDownloaded {len(mod_files)} files")
    
    # Save updated profile if needed
    if profile_updated:
        print("Updating profile with new version IDs...")
        if profile_manager.save_profile(profile):
            print("Profile updated successfully.")
    
    # Show cache locations
    print(f"\nMods are cached in: {config.get_cache_dir(minecraft_version, loader)}")
    if datapacks:
        print(f"Data packs are cached in: {config.get_datapack_cache_path(minecraft_version)}")

if __name__ == '__main__':
    main() 