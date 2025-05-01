#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
List mods in a modpack profile.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from core.profile_manager import ProfileManager
from core.mod_search import ModSearch

def main():
    """Handle listing mods in a profile."""
    parser = argparse.ArgumentParser(description='List mods in a profile.')
    parser.add_argument('--profile', required=True, help='Profile name')
    
    args = parser.parse_args()
    
    manager = ProfileManager()
    profile = manager.load_profile(args.profile)
    
    if not profile:
        print(f"Profile '{args.profile}' not found.")
        sys.exit(1)
    
    mod_search = ModSearch()
    
    # Print profile info
    print(f"Mods in profile: {args.profile}")
    print(f"Minecraft: {profile.get('minecraft_version')}")
    print(f"Loader: {profile.get('loader')} {profile.get('loader_version')}")
    print("")
    
    # Get mods from profile
    mods = profile.get('mods', [])
    
    if not mods:
        print("No mods in profile.")
        sys.exit(0)
    
    print(f"Total mods: {len(mods)}")
    print("")
    
    # Print mods
    for i, mod in enumerate(mods):
        mod_id = mod.get('id')
        mod_name = mod.get('name')
        mod_source = mod.get('source')
        mod_version = mod.get('version')
        
        print(f"{i+1}. {mod_name} (ID: {mod_id})")
        print(f"   Source: {mod_source}")
        if mod_version:
            print(f"   Version: {mod_version}")
        print("")

if __name__ == '__main__':
    main() 