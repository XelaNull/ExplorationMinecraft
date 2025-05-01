#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Check for compatible datapacks for the mods in a profile.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from lib.core.profile_manager import ProfileManager
from lib.core.mod_search import ModSearch
from lib.core.dependency_resolver import DependencyResolver

def main():
    """Handle checking for compatible datapacks."""
    parser = argparse.ArgumentParser(description='Check for compatible datapacks for the mods in a profile.')
    parser.add_argument('--profile', required=True, help='Profile name')
    parser.add_argument('--source', choices=['modrinth', 'curseforge', 'both'], default='both', help='Datapack source')
    
    args = parser.parse_args()
    
    manager = ProfileManager()
    mod_search = ModSearch()
    resolver = DependencyResolver()
    
    profile = manager.load_profile(args.profile)
    if not profile:
        print(f"Profile '{args.profile}' not found.")
        sys.exit(1)
    
    print(f"Checking for compatible datapacks for profile '{args.profile}'...")
    
    # Get mods from profile
    mods = profile.get('mods', [])
    if not mods:
        print("No mods found in profile.")
        sys.exit(0)
    
    # Get existing datapack IDs
    existing_datapacks = set(dp.get('id') for dp in profile.get('datapacks', []))
    
    # Get Minecraft version
    minecraft_version = profile.get('minecraft_version')
    
    # Check for datapacks for each mod
    found_datapacks = []
    
    print(f"Checking {len(mods)} mods for compatible datapacks...")
    
    for mod in mods:
        mod_name = mod.get('name')
        mod_id = mod.get('id')
        mod_source = mod.get('source')
        
        print(f"Checking {mod_name} ({mod_id})...")
        
        try:
            # Get mod details
            mod_details = None
            if mod_source == 'modrinth':
                # Try to get the project
                mod_details = mod_search.modrinth_api.get_mod(mod_id)
                if not mod_details:
                    # If using slug fails, we might need the project ID instead
                    for mod in profile.get('mods', []):
                        if mod.get('id') == mod_id and mod.get('version'):
                            # Try to get version info which might have the project ID
                            version_info = mod_search.modrinth_api._make_request(f"version/{mod.get('version')}")
                            if version_info and 'project_id' in version_info:
                                project_id = version_info.get('project_id')
                                print(f"  Using project ID {project_id} for mod {mod_id}")
                                mod_details = mod_search.modrinth_api.get_mod(project_id)
                                break
            elif mod_source == 'curseforge':
                mod_details = mod_search.curseforge_api.get_mod(mod_id)
            
            if not mod_details:
                print(f"  Warning: Could not get details for mod {mod_id}")
                continue
            
            # Get potential datapack IDs
            datapack_ids = resolver._extract_datapack_identifiers(mod_details, mod_source)
            
            for datapack_id in datapack_ids:
                if datapack_id in existing_datapacks:
                    print(f"  Datapack {datapack_id} already in profile")
                    continue
                
                # Try to find the datapack
                sources_to_try = []
                if args.source == 'both':
                    sources_to_try = ['modrinth', 'curseforge']
                else:
                    sources_to_try = [args.source]
                
                for source in sources_to_try:
                    try:
                        datapack_details = mod_search.get_mod_details(datapack_id, source)
                        if datapack_details:
                            # Get versions
                            versions = mod_search.get_mod_versions(
                                datapack_id, 
                                source, 
                                minecraft_version
                            )
                            
                            if versions:
                                # Found a compatible datapack
                                found_datapacks.append({
                                    'id': datapack_id,
                                    'name': datapack_details.get('name'),
                                    'source': source,
                                    'for_mod': mod_name
                                })
                                print(f"  Found datapack: {datapack_details.get('name')} ({source})")
                                break
                    except Exception as e:
                        print(f"  Warning: Error checking datapack {datapack_id} from {source}: {e}")
        except Exception as e:
            print(f"  Warning: Error processing mod {mod_id}: {e}")
    
    # Print results
    if found_datapacks:
        print(f"\nFound {len(found_datapacks)} compatible datapacks:")
        for i, dp in enumerate(found_datapacks):
            print(f"{i+1}. {dp.get('name')} (ID: {dp.get('id')}, Source: {dp.get('source')}) - For: {dp.get('for_mod')}")
        
        print("\nTo add a datapack: ./modpack_manager.sh add-datapack [datapack_id] --profile [profile] --source [source]")
    else:
        print("\nNo additional compatible datapacks found.")

if __name__ == '__main__':
    main() 