#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Profile manager for Minecraft Modpack Manager.
Handles creation, deletion, and management of modpack profiles.
Compatible with Python 2.7 and 3+.
"""

from __future__ import print_function, division, unicode_literals
import os
import sys
import json
import argparse
import datetime

# Add parent directory to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import config
from utils import logger
from utils import file_utils
from api.modrinth import ModrinthAPI
from api.curseforge import CurseForgeAPI
from core.mod_search import ModSearch
from core.dependency_resolver import DependencyResolver

# Python 2/3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    from io import open

class ProfileManager:
    """
    Manages modpack profiles.
    """
    
    def __init__(self):
        """Initialize APIs and utilities."""
        self.modrinth_api = ModrinthAPI()
        self.curseforge_api = CurseForgeAPI()
        self.mod_search = ModSearch()
        self.dependency_resolver = DependencyResolver()
    
    def create_profile(self, name, minecraft_version, loader, loader_version, description=None):
        """
        Create a new modpack profile.
        
        Args:
            name (str): Profile name
            minecraft_version (str): Minecraft version
            loader (str): Mod loader (fabric, forge)
            loader_version (str): Mod loader version
            description (str, optional): Profile description
            
        Returns:
            dict: Created profile data
        """
        # Validate inputs
        if not name or not minecraft_version or not loader or not loader_version:
            logger.error("Missing required parameters")
            return None
        
        # Check if profile already exists
        if self.profile_exists(name):
            logger.error(f"Profile '{name}' already exists")
            return None
        
        # Create profile object
        profile = {
            "name": name,
            "minecraft_version": minecraft_version,
            "loader": loader.lower(),
            "loader_version": loader_version,
            "description": description or f"{name} modpack for Minecraft {minecraft_version}",
            "created": datetime.datetime.now().isoformat(),
            "updated": datetime.datetime.now().isoformat(),
            "mods": [],
            "datapacks": [],
            "dependencies": []
        }
        
        # Save profile
        if self.save_profile(profile):
            logger.info(f"Created profile: {name}")
            return profile
        
        return None
    
    def load_profile(self, name):
        """
        Load a modpack profile.
        
        Args:
            name (str): Profile name
            
        Returns:
            dict: Profile data if found, None otherwise
        """
        profile_path = config.get_profile_path(name)
        
        if not os.path.exists(profile_path):
            logger.error(f"Profile not found: {name}")
            return None
        
        # Load profile from JSON file
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            # Add datapacks list if it doesn't exist (for backward compatibility)
            if "datapacks" not in profile:
                profile["datapacks"] = []
                # Save the updated profile with datapacks field
                self.save_profile(profile)
                
            logger.debug(f"Loaded profile: {name}")
            return profile
        except Exception as e:
            logger.error(f"Error loading profile {name}: {e}")
            return None
    
    def save_profile(self, profile):
        """
        Save a modpack profile.
        
        Args:
            profile (dict): Profile data
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not profile or "name" not in profile:
            logger.error("Invalid profile data")
            return False
        
        # Update timestamp
        profile["updated"] = datetime.datetime.now().isoformat()
        
        # Save profile to JSON file
        profile_path = config.get_profile_path(profile["name"])
        
        try:
            # Ensure directory exists
            profile_dir = os.path.dirname(profile_path)
            if not os.path.exists(profile_dir):
                os.makedirs(profile_dir)
            
            # Write profile JSON
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2)
            
            logger.debug(f"Saved profile: {profile['name']}")
            return True
        except Exception as e:
            logger.error(f"Error saving profile {profile['name']}: {e}")
            return False
    
    def delete_profile(self, name):
        """
        Delete a modpack profile.
        
        Args:
            name (str): Profile name
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.profile_exists(name):
            logger.error(f"Profile not found: {name}")
            return False
        
        # Delete profile file
        profile_path = config.get_profile_path(name)
        
        try:
            os.remove(profile_path)
            logger.info(f"Deleted profile: {name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting profile {name}: {e}")
            return False
    
    def profile_exists(self, name):
        """
        Check if a profile exists.
        
        Args:
            name (str): Profile name
            
        Returns:
            bool: True if exists, False otherwise
        """
        profile_path = config.get_profile_path(name)
        return os.path.exists(profile_path)
    
    def list_profiles(self):
        """
        List all profiles.
        
        Returns:
            list: List of profile names
        """
        profiles_dir = config.get_profiles_dir()
        
        if not os.path.exists(profiles_dir):
            return []
        
        # Get all JSON files in profiles directory
        profiles = []
        for filename in os.listdir(profiles_dir):
            if filename.endswith('.json'):
                profile_name = filename[:-5]  # Remove .json extension
                profiles.append(profile_name)
        
        return sorted(profiles)
    
    def _resolve_profile_dependencies(self, profile):
        """
        Resolve dependencies for a profile, including mods and datapacks.
        
        Args:
            profile (dict): Profile data
            
        Returns:
            dict: Updated profile
        """
        # First resolve mod dependencies
        logger.info("Resolving mod dependencies...")
        profile = self.dependency_resolver.resolve_dependencies(profile)
        
        return profile
        
    def add_mod(self, profile_name, mod_id, source, side="both"):
        """
        Add a mod to a profile.
        
        Args:
            profile_name (str): Profile name
            mod_id (str): Mod ID or slug
            source (str): Mod source (modrinth, curseforge, both)
            side (str): Mod side (client, server, both)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Load profile
        profile = self.load_profile(profile_name)
        if not profile:
            return False
        
        # Check if mod already exists in profile
        for mod in profile.get('mods', []):
            if mod.get('id') == mod_id and mod.get('source').lower() == source.lower():
                logger.warning(f"Mod {mod_id} already exists in profile {profile_name}")
                # Update side if different
                if mod.get('side', 'both') != side:
                    mod['side'] = side
                    logger.info(f"Updated mod {mod_id} side to {side}")
                    self.save_profile(profile)
                # Resolve dependencies even if mod exists to ensure we have all dependencies and datapacks
                logger.info("Re-checking dependencies...")
                updated_profile = self._resolve_profile_dependencies(profile)
                if updated_profile != profile:
                    self.save_profile(updated_profile)
                return True
        
        # Get mod details
        try:
            # Try the specified source first
            mod_details = None
            versions = None
            
            # Set up sources to try - always try the specified source first
            sources_to_try = []
            if source.lower() == "both":
                sources_to_try = ["modrinth", "curseforge"]
            else:
                sources_to_try = [source.lower()]
                # Add fallback source if primary fails
                fallback_source = "curseforge" if source.lower() == "modrinth" else "modrinth"
                sources_to_try.append(fallback_source)
            
            # Try each source in order
            for current_source in sources_to_try:
                logger.info(f"Trying to find mod {mod_id} from {current_source}...")
                mod_details = self.mod_search.get_mod_details(mod_id, current_source)
                
                if mod_details:
                    # Get mod versions compatible with profile
                    minecraft_version = profile.get('minecraft_version')
                    loader = profile.get('loader')
                    
                    versions = self.mod_search.get_mod_versions(
                        mod_id, 
                        current_source, 
                        minecraft_version, 
                        loader
                    )
                    
                    if versions:
                        source = current_source  # Update source to the one that succeeded
                        break
                    else:
                        logger.warning(f"No compatible versions found for mod {mod_id} ({current_source})")
            
            if not mod_details:
                logger.error(f"Mod not found: {mod_id} (tried: {', '.join(sources_to_try)})")
                return False
            
            if not versions:
                logger.error(f"No compatible versions found for mod {mod_id} (tried: {', '.join(sources_to_try)})")
                return False
            
            # Use the newest compatible version
            version = versions[0]
            
            # Create mod entry
            mod_entry = {
                "name": mod_details.get('name'),
                "id": mod_id,
                "version": version.get('id'),
                "source": source.lower(),
                "side": side
            }
            
            # Add mod to profile
            if 'mods' not in profile:
                profile['mods'] = []
                
            profile['mods'].append(mod_entry)
            
            # Save profile
            if self.save_profile(profile):
                logger.info(f"Added mod {mod_details.get('name')} to profile {profile_name}")
                
                # Resolve dependencies and datapacks
                logger.info("Resolving dependencies and datapacks...")
                updated_profile = self._resolve_profile_dependencies(profile)
                if updated_profile != profile:
                    self.save_profile(updated_profile)
                
                return True
            
        except Exception as e:
            logger.error(f"Error adding mod {mod_id} to profile {profile_name}: {e}")
            return False
        
        return False
    
    def remove_mod(self, profile_name, mod_id):
        """
        Remove a mod from a profile.
        
        Args:
            profile_name (str): Profile name
            mod_id (str): Mod ID or slug
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Load profile
        profile = self.load_profile(profile_name)
        if not profile:
            return False
        
        # Find and remove mod
        mods = profile.get('mods', [])
        found = False
        
        for i, mod in enumerate(mods):
            if str(mod.get('id')) == str(mod_id):
                del mods[i]
                found = True
                break
        
        if not found:
            logger.error(f"Mod {mod_id} not found in profile {profile_name}")
            return False
        
        # Save profile
        if self.save_profile(profile):
            logger.info(f"Removed mod {mod_id} from profile {profile_name}")
            
            # Re-resolve dependencies
            logger.info("Re-resolving dependencies...")
            updated_profile = self.dependency_resolver.resolve_dependencies(profile)
            
            if updated_profile:
                self.save_profile(updated_profile)
            
            return True
        
        return False
    
    def add_datapack(self, profile_name, datapack_id, source):
        """
        Add a data pack to a profile.
        
        Args:
            profile_name (str): Profile name
            datapack_id (str): Data pack ID or slug
            source (str): Data pack source (modrinth, curseforge, both)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Load profile
        profile = self.load_profile(profile_name)
        if not profile:
            return False
        
        # Check if datapack already exists in profile
        for datapack in profile.get('datapacks', []):
            if datapack.get('id') == datapack_id and datapack.get('source').lower() == source.lower():
                logger.warning(f"Data pack {datapack_id} already exists in profile {profile_name}")
                return True
        
        # Get datapack details
        try:
            # Try the specified source first
            datapack_details = None
            versions = None
            
            # Set up sources to try - always try the specified source first
            sources_to_try = []
            if source.lower() == "both":
                sources_to_try = ["modrinth", "curseforge"]
            else:
                sources_to_try = [source.lower()]
                # Add fallback source if primary fails
                fallback_source = "curseforge" if source.lower() == "modrinth" else "modrinth"
                sources_to_try.append(fallback_source)
            
            # Try each source in order
            for current_source in sources_to_try:
                logger.info(f"Trying to find datapack {datapack_id} from {current_source}...")
                datapack_details = self.mod_search.get_mod_details(datapack_id, current_source)
                
                if datapack_details:
                    # Get datapack versions compatible with profile
                    game_version = profile.get('minecraft_version')
                    
                    versions = self.mod_search.get_mod_versions(
                        datapack_id, 
                        current_source, 
                        game_version
                    )
                    
                    if versions:
                        source = current_source  # Update source to the one that succeeded
                        break
                    else:
                        logger.warning(f"No compatible versions found for datapack {datapack_id} ({current_source})")
            
            if not datapack_details:
                logger.error(f"Data pack not found: {datapack_id} (tried: {', '.join(sources_to_try)})")
                return False
            
            if not versions:
                logger.error(f"No compatible versions found for data pack {datapack_id} (tried: {', '.join(sources_to_try)})")
                return False
            
            # Use the newest compatible version
            version = versions[0]
            
            # Create datapack entry
            datapack_entry = {
                "name": datapack_details.get('name'),
                "id": datapack_id,
                "version": version.get('id'),
                "source": source.lower()
            }
            
            # Add datapack to profile
            if 'datapacks' not in profile:
                profile['datapacks'] = []
                
            profile['datapacks'].append(datapack_entry)
            
            # Save profile
            if self.save_profile(profile):
                logger.info(f"Added data pack {datapack_details.get('name')} to profile {profile_name}")
                return True
        except Exception as e:
            logger.error(f"Error adding data pack {datapack_id} to profile {profile_name}: {e}")
            return False
        
        return False
    
    def remove_datapack(self, profile_name, datapack_id):
        """
        Remove a data pack from a profile.
        
        Args:
            profile_name (str): Profile name
            datapack_id (str): Data pack ID or slug
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Load profile
        profile = self.load_profile(profile_name)
        if not profile:
            return False
        
        # Find and remove datapack
        datapacks = profile.get('datapacks', [])
        found = False
        
        for i, datapack in enumerate(datapacks):
            if str(datapack.get('id')) == str(datapack_id):
                del datapacks[i]
                found = True
                break
        
        if not found:
            logger.error(f"Data pack {datapack_id} not found in profile {profile_name}")
            return False
        
        # Save profile
        if self.save_profile(profile):
            logger.info(f"Removed data pack {datapack_id} from profile {profile_name}")
            return True
        
        return False
    
    def list_datapacks(self, profile_name):
        """
        List data packs in a profile.
        
        Args:
            profile_name (str): Profile name
            
        Returns:
            list: List of data pack entries
        """
        # Load profile
        profile = self.load_profile(profile_name)
        if not profile:
            return []
        
        return profile.get('datapacks', [])

def create(args):
    """Command to create a new profile."""
    parser = argparse.ArgumentParser(description='Create a new modpack profile.')
    parser.add_argument('name', help='Profile name')
    parser.add_argument('--minecraft', required=True, help='Minecraft version')
    parser.add_argument('--loader', required=True, choices=['fabric', 'forge'], help='Mod loader')
    parser.add_argument('--loader-version', required=True, help='Mod loader version')
    parser.add_argument('--description', help='Profile description')
    
    try:
        parsed_args = parser.parse_args(args)
        
        manager = ProfileManager()
        profile = manager.create_profile(
            parsed_args.name,
            parsed_args.minecraft,
            parsed_args.loader,
            parsed_args.loader_version,
            parsed_args.description
        )
        
        if profile:
            print(f"Profile '{parsed_args.name}' created successfully.")
        else:
            print(f"Failed to create profile '{parsed_args.name}'.")
    except Exception as e:
        print(f"Error: {e}")

def delete(args):
    """Command to delete a profile."""
    parser = argparse.ArgumentParser(description='Delete a modpack profile.')
    parser.add_argument('name', help='Profile name')
    
    try:
        parsed_args = parser.parse_args(args)
        
        manager = ProfileManager()
        if manager.delete_profile(parsed_args.name):
            print(f"Profile '{parsed_args.name}' deleted successfully.")
        else:
            print(f"Failed to delete profile '{parsed_args.name}'.")
    except Exception as e:
        print(f"Error: {e}")

def list_profiles(args):
    """Command to list all profiles."""
    parser = argparse.ArgumentParser(description='List all modpack profiles.')
    
    try:
        manager = ProfileManager()
        profiles = manager.list_profiles()
        
        if profiles:
            print("Available modpack profiles:")
            for i, name in enumerate(profiles):
                print(f"{i+1}. {name}")
        else:
            print("No modpack profiles found.")
    except Exception as e:
        print(f"Error: {e}")

def show(args):
    """Command to show profile details."""
    parser = argparse.ArgumentParser(description='Show modpack profile details.')
    parser.add_argument('name', help='Profile name')
    
    try:
        parsed_args = parser.parse_args(args)
        
        manager = ProfileManager()
        profile = manager.load_profile(parsed_args.name)
        
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
                print(f"{i+1}. {mod.get('name')} ({mod.get('source')})")
                
            datapacks = profile.get('datapacks', [])
            print(f"\nData Packs ({len(datapacks)}):")
            for i, datapack in enumerate(datapacks):
                print(f"{i+1}. {datapack.get('name')} ({datapack.get('source')})")
            
            dependencies = profile.get('dependencies', [])
            print(f"\nDependencies ({len(dependencies)}):")
            for i, dep in enumerate(dependencies):
                required_by = ', '.join(dep.get('required_by', []))
                print(f"{i+1}. {dep.get('name')} - Required by: {required_by}")
        else:
            print(f"Profile '{parsed_args.name}' not found.")
    except Exception as e:
        print(f"Error: {e}")

def add_mod(args):
    """Command to add a mod to a profile."""
    parser = argparse.ArgumentParser(description='Add a mod to a profile.')
    parser.add_argument('mod_id', help='Mod ID or slug')
    parser.add_argument('--profile', required=True, help='Profile name')
    parser.add_argument('--source', required=True, choices=['modrinth', 'curseforge'], help='Mod source')
    
    try:
        parsed_args = parser.parse_args(args)
        
        manager = ProfileManager()
        if manager.add_mod(parsed_args.profile, parsed_args.mod_id, parsed_args.source):
            print(f"Mod '{parsed_args.mod_id}' added to profile '{parsed_args.profile}'.")
        else:
            print(f"Failed to add mod '{parsed_args.mod_id}' to profile '{parsed_args.profile}'.")
    except Exception as e:
        print(f"Error: {e}")

def remove_mod(args):
    """Command to remove a mod from a profile."""
    parser = argparse.ArgumentParser(description='Remove a mod from a profile.')
    parser.add_argument('mod_id', help='Mod ID or slug')
    parser.add_argument('--profile', required=True, help='Profile name')
    
    try:
        parsed_args = parser.parse_args(args)
        
        manager = ProfileManager()
        if manager.remove_mod(parsed_args.profile, parsed_args.mod_id):
            print(f"Mod '{parsed_args.mod_id}' removed from profile '{parsed_args.profile}'.")
        else:
            print(f"Failed to remove mod '{parsed_args.mod_id}' from profile '{parsed_args.profile}'.")
    except Exception as e:
        print(f"Error: {e}")

def list_mods(args):
    """Command to list mods in a profile."""
    parser = argparse.ArgumentParser(description='List mods in a profile.')
    parser.add_argument('--profile', required=True, help='Profile name')
    
    try:
        parsed_args = parser.parse_args(args)
        
        manager = ProfileManager()
        profile = manager.load_profile(parsed_args.profile)
        
        if profile:
            mods = profile.get('mods', [])
            dependencies = profile.get('dependencies', [])
            
            print(f"Mods in profile '{parsed_args.profile}':")
            print("\nDirect mods:")
            for i, mod in enumerate(mods):
                print(f"{i+1}. {mod.get('name')} ({mod.get('source')})")
            
            print("\nDependencies:")
            for i, dep in enumerate(dependencies):
                required_by = ', '.join(dep.get('required_by', []))
                print(f"{i+1}. {dep.get('name')} - Required by: {required_by}")
        else:
            print(f"Profile '{parsed_args.profile}' not found.")
    except Exception as e:
        print(f"Error: {e}")

def add_datapack(args):
    """Command to add a data pack to a profile."""
    parser = argparse.ArgumentParser(description='Add a data pack to a profile.')
    parser.add_argument('datapack_id', help='Data pack ID or slug')
    parser.add_argument('--profile', required=True, help='Profile name')
    parser.add_argument('--source', required=True, choices=['modrinth', 'curseforge'], help='Data pack source')
    
    try:
        parsed_args = parser.parse_args(args)
        
        manager = ProfileManager()
        if manager.add_datapack(parsed_args.profile, parsed_args.datapack_id, parsed_args.source):
            print(f"Data pack '{parsed_args.datapack_id}' added to profile '{parsed_args.profile}'.")
        else:
            print(f"Failed to add data pack '{parsed_args.datapack_id}' to profile '{parsed_args.profile}'.")
    except Exception as e:
        print(f"Error: {e}")

def remove_datapack(args):
    """Command to remove a data pack from a profile."""
    parser = argparse.ArgumentParser(description='Remove a data pack from a profile.')
    parser.add_argument('datapack_id', help='Data pack ID or slug')
    parser.add_argument('--profile', required=True, help='Profile name')
    
    try:
        parsed_args = parser.parse_args(args)
        
        manager = ProfileManager()
        if manager.remove_datapack(parsed_args.profile, parsed_args.datapack_id):
            print(f"Data pack '{parsed_args.datapack_id}' removed from profile '{parsed_args.profile}'.")
        else:
            print(f"Failed to remove data pack '{parsed_args.datapack_id}' from profile '{parsed_args.profile}'.")
    except Exception as e:
        print(f"Error: {e}")

def list_datapacks(args):
    """Command to list data packs in a profile."""
    parser = argparse.ArgumentParser(description='List data packs in a profile.')
    parser.add_argument('--profile', required=True, help='Profile name')
    
    try:
        parsed_args = parser.parse_args(args)
        
        manager = ProfileManager()
        profile = manager.load_profile(parsed_args.profile)
        
        if profile:
            datapacks = profile.get('datapacks', [])
            
            print(f"Data packs in profile '{parsed_args.profile}':")
            if datapacks:
                for i, datapack in enumerate(datapacks):
                    print(f"{i+1}. {datapack.get('name')} ({datapack.get('source')})")
            else:
                print("No data packs found in this profile.")
        else:
            print(f"Profile '{parsed_args.profile}' not found.")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Test profile management functionality."""
    manager = ProfileManager()
    
    print("Testing profile management...")
    
    # Create profile
    profile = manager.create_profile("test_profile", "1.20.1", "fabric", "0.14.21")
    
    if profile:
        # Add mods
        manager.add_mod("test_profile", "create-fabric", "modrinth")
        
        # Add datapacks
        manager.add_datapack("test_profile", "terralith", "modrinth")
        
        # Show profile
        show(["test_profile"])
        
        # List profiles
        list_profiles([])
        
        # Delete profile
        manager.delete_profile("test_profile")
    
if __name__ == '__main__':
    main() 