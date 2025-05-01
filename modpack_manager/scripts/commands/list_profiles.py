#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
List all available modpack profiles.
"""

import sys
import os
import argparse

# Add parent directory to path for module imports
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(lib_path)

from core.profile_manager import ProfileManager

def main():
    """Handle the list profiles command."""
    parser = argparse.ArgumentParser(description='List all modpack profiles.')
    
    # Parse args (no args needed for this command but keeping the structure)
    args = parser.parse_args()
    
    manager = ProfileManager()
    profiles = manager.list_profiles()
    
    if profiles:
        print("Available modpack profiles:")
        for i, name in enumerate(profiles):
            print(f"{i+1}. {name}")
    else:
        print("No modpack profiles found.")

if __name__ == '__main__':
    main() 