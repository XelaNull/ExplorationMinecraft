#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Remove a mod from a modpack profile.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from lib.core.profile_manager import ProfileManager

def main():
    """Handle the remove mod command."""
    parser = argparse.ArgumentParser(description='Remove a mod from a profile.')
    parser.add_argument('mod_id', help='Mod ID or slug to remove')
    parser.add_argument('--profile', required=True, help='Profile name')
    
    args = parser.parse_args()
    
    manager = ProfileManager()
    if manager.remove_mod(args.profile, args.mod_id):
        print(f"Mod '{args.mod_id}' removed from profile '{args.profile}'.")
    else:
        print(f"Failed to remove mod '{args.mod_id}' from profile '{args.profile}'.")
        sys.exit(1)

if __name__ == '__main__':
    main() 