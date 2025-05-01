#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Show modpack profile details.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from lib.core.profile_manager import ProfileManager

def main():
    """Handle showing profile details."""
    parser = argparse.ArgumentParser(description='Show modpack profile details.')
    parser.add_argument('name', help='Profile name')
    
    args = parser.parse_args()
    
    manager = ProfileManager()
    profile = manager.load_profile(args.name)
    
    if profile:
        print(f"Profile: {profile.get('name')}")
        print(f"Minecraft: {profile.get('minecraft_version')}")
        print(f"Loader: {profile.get('loader')} {profile.get('loader_version')}")
        print(f"Description: {profile.get('description')}")
        print(f"Created: {profile.get('created')}")
        print(f"Updated: {profile.get('updated')}")
        
        mods = profile.get('mods', [])
        print(f"\nMods ({len(mods)}):")
        for i, mod in enumerate(mods):
            side = mod.get('side', 'both')
            side_str = f" [{side}]" if side != 'both' else ""
            print(f"{i+1}. {mod.get('name')} ({mod.get('source')}){side_str}")
            
        datapacks = profile.get('datapacks', [])
        print(f"\nData Packs ({len(datapacks)}):")
        if datapacks:
            for i, datapack in enumerate(datapacks):
                print(f"{i+1}. {datapack.get('name')} ({datapack.get('source')})")
        else:
            print("No data packs in this profile.")
        
        dependencies = profile.get('dependencies', [])
        print(f"\nDependencies ({len(dependencies)}):")
        for i, dep in enumerate(dependencies):
            required_by = ', '.join(dep.get('required_by', []))
            print(f"{i+1}. {dep.get('name')} - Required by: {required_by}")
    else:
        print(f"Profile '{args.name}' not found.")
        sys.exit(1)

if __name__ == '__main__':
    main() 