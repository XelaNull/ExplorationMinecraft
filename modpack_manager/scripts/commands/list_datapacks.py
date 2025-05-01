#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
List data packs in a modpack profile.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from lib.core.profile_manager import ProfileManager

def main():
    """Handle listing data packs in a profile."""
    parser = argparse.ArgumentParser(description='List data packs in a profile.')
    parser.add_argument('--profile', required=True, help='Profile name')
    
    args = parser.parse_args()
    
    manager = ProfileManager()
    
    profile = manager.load_profile(args.profile)
    if not profile:
        print(f"Profile '{args.profile}' not found.")
        sys.exit(1)
        
    datapacks = profile.get('datapacks', [])
    
    print(f"Data packs in profile '{args.profile}':")
    if datapacks:
        for i, datapack in enumerate(datapacks):
            print(f"{i+1}. {datapack.get('name')} ({datapack.get('source')})")
    else:
        print("No data packs found in this profile.")

if __name__ == '__main__':
    main() 