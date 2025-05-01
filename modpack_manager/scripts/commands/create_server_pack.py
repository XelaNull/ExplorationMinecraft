#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Create a server-side modpack for deployment to Docker.
Prepares server-side and both-side mods in the server_pack directory.
"""

import sys
import os
import argparse
import shutil
import json
from datetime import datetime

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from lib.core.profile_manager import ProfileManager
from lib.core.downloader import ModDownloader
from utils import config
from utils import file_utils

def main():
    """Handle creating a server-side modpack."""
    parser = argparse.ArgumentParser(description='Create a server-side modpack for Docker deployment.')
    parser.add_argument('--profile', required=True, help='Profile name')
    parser.add_argument('--force', action='store_true', help='Force recreation of server pack even if it exists')
    
    args = parser.parse_args()
    
    profile_manager = ProfileManager()
    profile = profile_manager.load_profile(args.profile)
    
    if not profile:
        print(f"Profile '{args.profile}' not found.")
        sys.exit(1)
    
    minecraft_version = profile.get('minecraft_version')
    loader = profile.get('loader')
    loader_version = profile.get('loader_version')
    
    print(f"Creating server pack for profile '{args.profile}'")
    print(f"Minecraft: {minecraft_version}")
    print(f"Loader: {loader} {loader_version}")
    
    # Set up paths
    server_pack_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'server_pack')
    server_mods_dir = os.path.join(server_pack_dir, 'mods')
    server_config_dir = os.path.join(server_pack_dir, 'config')
    server_datapacks_dir = os.path.join(server_pack_dir, 'datapacks')
    
    # Check if server pack directory exists and force option is not set
    if os.path.exists(server_pack_dir) and not args.force:
        confirm = input(f"Server pack directory already exists. Overwrite? (y/N): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            sys.exit(0)
    
    # Create or clean server pack directories
    if os.path.exists(server_pack_dir):
        print("Cleaning existing server pack directory...")
        for item in os.listdir(server_mods_dir):
            item_path = os.path.join(server_mods_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
        
        for item in os.listdir(server_datapacks_dir):
            item_path = os.path.join(server_datapacks_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
    else:
        print("Creating server pack directories...")
        os.makedirs(server_pack_dir, exist_ok=True)
        os.makedirs(server_mods_dir, exist_ok=True)
        os.makedirs(server_config_dir, exist_ok=True)
        os.makedirs(server_datapacks_dir, exist_ok=True)
    
    # Make sure mods are downloaded
    print("Ensuring all mods are downloaded...")
    downloader = ModDownloader()
    
    # Determine which mods to include
    server_mods = []
    both_mods = []
    dependencies = []
    datapacks = profile.get('datapacks', [])
    
    # Process mods based on side
    for mod in profile.get('mods', []):
        side = mod.get('side', 'both').lower()
        if side == 'server' or side == 'both':
            if side == 'server':
                server_mods.append(mod)
            else:
                both_mods.append(mod)
    
    # Include dependencies
    for dep in profile.get('dependencies', []):
        dependencies.append(dep)
    
    # Create mod list for tracking
    included_mods = []
    
    # Copy server-side mods
    print(f"Including {len(server_mods)} server-only mods...")
    for mod in server_mods:
        file_path, version_id = downloader.download_mod(mod, minecraft_version, loader)
        if file_path and os.path.exists(file_path):
            dest_path = os.path.join(server_mods_dir, os.path.basename(file_path))
            shutil.copy2(file_path, dest_path)
            included_mods.append({
                "name": mod.get('name'),
                "id": mod.get('id'),
                "version": version_id,
                "source": mod.get('source'),
                "side": "server"
            })
            print(f"  Added {mod.get('name')}")
    
    # Copy both-sides mods
    print(f"Including {len(both_mods)} both-sides mods...")
    for mod in both_mods:
        file_path, version_id = downloader.download_mod(mod, minecraft_version, loader)
        if file_path and os.path.exists(file_path):
            dest_path = os.path.join(server_mods_dir, os.path.basename(file_path))
            shutil.copy2(file_path, dest_path)
            included_mods.append({
                "name": mod.get('name'),
                "id": mod.get('id'),
                "version": version_id,
                "source": mod.get('source'),
                "side": "both"
            })
            print(f"  Added {mod.get('name')}")
    
    # Copy dependencies
    print(f"Including {len(dependencies)} dependencies...")
    for dep in dependencies:
        file_path, version_id = downloader.download_mod(dep, minecraft_version, loader)
        if file_path and os.path.exists(file_path):
            dest_path = os.path.join(server_mods_dir, os.path.basename(file_path))
            shutil.copy2(file_path, dest_path)
            included_mods.append({
                "name": dep.get('name'),
                "id": dep.get('id'),
                "version": version_id,
                "source": dep.get('source'),
                "side": "both",
                "required_by": dep.get('required_by', [])
            })
            print(f"  Added {dep.get('name')}")
    
    # Copy datapacks
    if datapacks:
        print(f"Including {len(datapacks)} data packs...")
        for datapack in datapacks:
            file_path, version_id = downloader.download_datapack(datapack, minecraft_version)
            if file_path and os.path.exists(file_path):
                # For datapacks in server, remove any file extension and use .zip if not present
                datapack_name = os.path.basename(file_path)
                if datapack_name.endswith('.jar.zip'): 
                    datapack_name = datapack_name[:-8] + '.zip'  # Convert .jar.zip to .zip
                
                dest_path = os.path.join(server_datapacks_dir, datapack_name)
                shutil.copy2(file_path, dest_path)
                print(f"  Added {datapack.get('name')}")
    
    # Create metadata file
    metadata = {
        "name": profile.get('name'),
        "description": profile.get('description'),
        "minecraft_version": minecraft_version,
        "loader": loader,
        "loader_version": loader_version,
        "created": datetime.now().isoformat(),
        "mods": included_mods,
        "datapacks": datapacks
    }
    
    with open(os.path.join(server_pack_dir, 'server-manifest.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Create default server.properties file if it doesn't exist
    server_properties_path = os.path.join(server_pack_dir, 'server.properties')
    if not os.path.exists(server_properties_path):
        with open(server_properties_path, 'w') as f:
            f.write(f"""# Minecraft server properties for {profile.get('name')}
# Created: {datetime.now().strftime('%Y-%m-%d')}
spawn-protection=16
max-tick-time=60000
query.port=25565
generator-settings=
sync-chunk-writes=true
force-gamemode=false
allow-nether=true
enforce-whitelist=false
gamemode=survival
broadcast-console-to-ops=true
enable-query=false
player-idle-timeout=0
text-filtering-config=
difficulty=easy
spawn-monsters=true
broadcast-rcon-to-ops=true
op-permission-level=4
pvp=true
entity-broadcast-range-percentage=100
snooper-enabled=true
level-type=default
hardcore=false
enable-status=true
enable-command-block=true
max-players=20
network-compression-threshold=256
resource-pack-sha1=
max-world-size=29999984
function-permission-level=2
rcon.port=25575
server-port=25565
server-ip=
spawn-npcs=true
allow-flight=false
level-name=world
view-distance=10
resource-pack=
spawn-animals=true
white-list=false
rcon.password=
generate-structures=true
max-build-height=256
online-mode=true
level-seed=
use-native-transport=true
prevent-proxy-connections=false
enable-jmx-monitoring=false
enable-rcon=false
rate-limit=0
motd=A {profile.get('name')} Server
""")
    
    # Create empty ops.json file if it doesn't exist
    ops_path = os.path.join(server_pack_dir, 'ops.json')
    if not os.path.exists(ops_path):
        with open(ops_path, 'w') as f:
            f.write("[]")
    
    # Create empty whitelist.json file if it doesn't exist
    whitelist_path = os.path.join(server_pack_dir, 'whitelist.json')
    if not os.path.exists(whitelist_path):
        with open(whitelist_path, 'w') as f:
            f.write("[]")
    
    print(f"\nServer pack created successfully in: {server_pack_dir}")
    print(f"Includes {len(included_mods)} mods and {len(datapacks)} datapacks")
    print("\nThis server pack is ready to be built into a Docker image with:")
    print(f"  ./scripts/docker_image_manager.sh build {args.profile}")

if __name__ == '__main__':
    main() 