#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Create a client-side modpack for distribution.
Packages client-side and both-side mods into a ZIP file.
"""

import sys
import os
import argparse
import zipfile
import shutil
import tempfile
import json
from datetime import datetime

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from core.profile_manager import ProfileManager
from core.downloader import ModDownloader
from utils import config
from utils import file_utils

def main():
    """Handle creating a client-side modpack."""
    parser = argparse.ArgumentParser(description='Create a client-side modpack for distribution.')
    parser.add_argument('--profile', required=True, help='Profile name')
    parser.add_argument('--output', help='Output ZIP file path (default: client_packs/<profile>.zip)')
    parser.add_argument('--include-config', action='store_true', help='Include config files in the pack')
    
    args = parser.parse_args()
    
    profile_manager = ProfileManager()
    profile = profile_manager.load_profile(args.profile)
    
    if not profile:
        print(f"Profile '{args.profile}' not found.")
        sys.exit(1)
    
    minecraft_version = profile.get('minecraft_version')
    loader = profile.get('loader')
    loader_version = profile.get('loader_version')
    
    print(f"Creating client-side modpack for profile '{args.profile}'")
    print(f"Minecraft: {minecraft_version}")
    print(f"Loader: {loader} {loader_version}")
    
    # Make sure mods are downloaded
    print("Ensuring all mods are downloaded...")
    downloader = ModDownloader()
    
    # Determine which mods to include
    client_mods = []
    both_mods = []
    dependencies = []
    datapacks = profile.get('datapacks', [])
    
    # Process mods based on side
    for mod in profile.get('mods', []):
        side = mod.get('side', 'both').lower()
        if side == 'client' or side == 'both':
            if side == 'client':
                client_mods.append(mod)
            else:
                both_mods.append(mod)
    
    # Include dependencies
    for dep in profile.get('dependencies', []):
        dependencies.append(dep)
    
    # Create a temporary directory for building the pack
    with tempfile.TemporaryDirectory() as temp_dir:
        mods_dir = os.path.join(temp_dir, 'mods')
        config_dir = os.path.join(temp_dir, 'config')
        resourcepacks_dir = os.path.join(temp_dir, 'resourcepacks')
        
        # Create directories
        os.makedirs(mods_dir, exist_ok=True)
        os.makedirs(config_dir, exist_ok=True)
        os.makedirs(resourcepacks_dir, exist_ok=True)
        
        # Create mod list for tracking
        included_mods = []
        
        # Copy client-side mods
        print(f"Including {len(client_mods)} client-only mods...")
        for mod in client_mods:
            file_path, version_id = downloader.download_mod(mod, minecraft_version, loader)
            if file_path and os.path.exists(file_path):
                dest_path = os.path.join(mods_dir, os.path.basename(file_path))
                shutil.copy2(file_path, dest_path)
                included_mods.append({
                    "name": mod.get('name'),
                    "id": mod.get('id'),
                    "version": version_id,
                    "source": mod.get('source'),
                    "side": "client"
                })
        
        # Copy both-sides mods
        print(f"Including {len(both_mods)} both-sides mods...")
        for mod in both_mods:
            file_path, version_id = downloader.download_mod(mod, minecraft_version, loader)
            if file_path and os.path.exists(file_path):
                dest_path = os.path.join(mods_dir, os.path.basename(file_path))
                shutil.copy2(file_path, dest_path)
                included_mods.append({
                    "name": mod.get('name'),
                    "id": mod.get('id'),
                    "version": version_id,
                    "source": mod.get('source'),
                    "side": "both"
                })
        
        # Copy dependencies
        print(f"Including {len(dependencies)} dependencies...")
        for dep in dependencies:
            file_path, version_id = downloader.download_mod(dep, minecraft_version, loader)
            if file_path and os.path.exists(file_path):
                dest_path = os.path.join(mods_dir, os.path.basename(file_path))
                shutil.copy2(file_path, dest_path)
                included_mods.append({
                    "name": dep.get('name'),
                    "id": dep.get('id'),
                    "version": version_id,
                    "source": dep.get('source'),
                    "side": "both",
                    "required_by": dep.get('required_by', [])
                })
        
        # Copy datapacks (they go in a resourcepacks directory for client packs)
        if datapacks:
            print(f"Including {len(datapacks)} data packs...")
            for datapack in datapacks:
                file_path, version_id = downloader.download_datapack(datapack, minecraft_version)
                if file_path and os.path.exists(file_path):
                    dest_path = os.path.join(resourcepacks_dir, os.path.basename(file_path))
                    shutil.copy2(file_path, dest_path)
        
        # Create metadata file
        metadata = {
            "name": profile.get('name'),
            "description": profile.get('description'),
            "minecraft_version": minecraft_version,
            "loader": loader,
            "loader_version": loader_version,
            "created": datetime.now().isoformat(),
            "mods": included_mods
        }
        
        with open(os.path.join(temp_dir, 'modpack.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create README file with installation instructions
        readme_content = f"""# {profile.get('name')} Client Pack

## Information
- Minecraft Version: {minecraft_version}
- Mod Loader: {loader.capitalize()} {loader_version}
- Created: {datetime.now().strftime('%Y-%m-%d')}

## Installation Instructions
1. Install {loader.capitalize()} {loader_version} for Minecraft {minecraft_version}
2. Extract this ZIP file into your Minecraft instance directory
3. Launch Minecraft with the {loader.capitalize()} profile

## Mods Included
Total: {len(included_mods)}

"""
        
        for mod in included_mods:
            readme_content += f"- {mod.get('name')} ({mod.get('source')})\n"
        
        with open(os.path.join(temp_dir, 'README.txt'), 'w') as f:
            f.write(readme_content)
        
        # Determine output path
        if args.output:
            output_path = args.output
        else:
            output_path = config.get_client_pack_path(args.profile)
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create ZIP file
        print(f"Creating client pack: {output_path}")
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, rel_path)
        
        print(f"Client pack created: {output_path}")
        print(f"Includes {len(included_mods)} mods")

if __name__ == '__main__':
    main() 