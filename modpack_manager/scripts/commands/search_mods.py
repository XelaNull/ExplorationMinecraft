#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Search for mods in Modrinth and CurseForge.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from core.mod_search import ModSearch
from core.profile_manager import ProfileManager

def main():
    """Handle searching for mods."""
    parser = argparse.ArgumentParser(description='Search for mods.')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--profile', required=True, help='Profile name')
    parser.add_argument('--source', choices=['modrinth', 'curseforge', 'both'], default='both', help='Mod source')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of results')
    
    args = parser.parse_args()
    
    manager = ProfileManager()
    profile = manager.load_profile(args.profile)
    
    if not profile:
        print(f"Profile '{args.profile}' not found.")
        sys.exit(1)
    
    mod_search = ModSearch()
    
    # Get search parameters from profile
    minecraft_version = profile.get('minecraft_version')
    loader = profile.get('loader')
    
    print(f"Searching for: {args.query}")
    print(f"Minecraft: {minecraft_version}")
    print(f"Loader: {loader}")
    print(f"Source: {args.source}")
    print("")
    
    # Search in Modrinth
    if args.source in ['modrinth', 'both']:
        print("=== Modrinth Results ===")
        print(f"Searching Modrinth for '{args.query}'...")
        modrinth_results = mod_search.search_modrinth(
            args.query,
            minecraft_version,
            loader,
            args.limit
        )
        
        if modrinth_results:
            for i, mod in enumerate(modrinth_results):
                # Using slug or project_id, whichever is available
                mod_id = mod.get('slug') or mod.get('project_id')
                mod_title = mod.get('title')
                mod_description = mod.get('description', '')[:100] + "..." if len(mod.get('description', '')) > 100 else mod.get('description', '')
                mod_downloads = mod.get('downloads', 'N/A')
                print(f"{i+1}. {mod_title} (ID: {mod_id})")
                print(f"   Description: {mod_description}")
                print(f"   Downloads: {mod_downloads}")
                print("")
        else:
            print("No results found.")
            
        print("")
    
    # Search in CurseForge
    if args.source in ['curseforge', 'both']:
        print("=== CurseForge Results ===")
        curseforge_results = mod_search.search_curseforge(
            args.query,
            minecraft_version,
            loader,
            args.limit
        )
        
        if curseforge_results:
            for i, mod in enumerate(curseforge_results):
                # Ensure we have the mod ID as a string
                mod_id = str(mod.get('id', ''))
                mod_name = mod.get('name', 'Unknown Mod')
                mod_slug = mod.get('slug', '')
                mod_description = mod.get('description', 'No description')
                if len(mod_description) > 100:
                    mod_description = mod_description[:100] + "..."
                mod_downloads = mod.get('downloads', 'N/A')
                mod_loaders = mod.get('loaders', [])
                
                print(f"{i+1}. {mod_name} (ID: {mod_id}, Slug: {mod_slug})")
                print(f"   Description: {mod_description}")
                print(f"   Downloads: {mod_downloads}")
                if mod_loaders:
                    print(f"   Loaders: {', '.join(mod_loaders)}")
                print("")
        else:
            print("No results found.")
    
    print("To add a mod: ./modpack_manager.sh add [mod_id] --profile [profile] --source [source]")

if __name__ == '__main__':
    main() 