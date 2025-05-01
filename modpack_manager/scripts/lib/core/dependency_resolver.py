#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dependency resolver for Minecraft Modpack Manager.
Handles resolving mod dependencies for both Modrinth and CurseForge mods.
Compatible with Python 2.7 and 3+.
"""

from __future__ import print_function, division, unicode_literals
import os
import sys
import json
from collections import deque

# Add parent directory to path for module imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import config
from api.modrinth import ModrinthAPI
from api.curseforge import CurseForgeAPI

# Python 2/3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    from io import open

class DependencyResolver:
    """
    Handles resolving mod dependencies.
    """
    
    def __init__(self):
        """Initialize API clients."""
        self.modrinth_api = ModrinthAPI()
        self.curseforge_api = CurseForgeAPI()
    
    # Modified method to be more conservative about datapack detection
    def _extract_datapack_identifiers(self, mod_details, mod_source, file_info=None):
        """
        Extract potential datapack identifiers from mod details.
        Only includes datapacks with strong evidence they are needed.
        
        Args:
            mod_details (dict): Mod details from API
            mod_source (str): Source of the mod (modrinth or curseforge)
            file_info (dict, optional): Specific file information for the mod
            
        Returns:
            list: List of datapack identifiers
        """
        datapack_ids = []
        mod_id = mod_details.get('id')
        mod_name = mod_details.get('name', '').lower()
        mod_slug = mod_details.get('slug', '').lower()
        
        # List of verified datapacks that actually exist and have strong evidence
        # Format: (mod_name_contains, datapack_id, source)
        KNOWN_DATAPACK_MAPPING = [
            ('quark', 'quark-oddities', 'modrinth'),
            ('create', 'createplus', 'modrinth')
        ]
        
        # Log the mappings for debugging
        print(f"Checking for known datapack mappings for mod: {mod_name}")
        for mapping in KNOWN_DATAPACK_MAPPING:
            mod_pattern, dp_id, src = mapping
            if mod_pattern in mod_name or mod_pattern in mod_slug:
                print(f"  Found datapack mapping: {mod_pattern} -> {dp_id} ({src})")
        
        # Check if this mod has a known datapack
        for mod_pattern, datapack_id, source in KNOWN_DATAPACK_MAPPING:
            if mod_pattern in mod_name or mod_pattern in mod_slug:
                if source.lower() == mod_source.lower():
                    datapack_ids.append(datapack_id)
        
        # Check description for very strong references to required datapacks
        description = mod_details.get('description', '') + mod_details.get('body', '')
        description = description.lower()
        
        # Only look for very explicit mentions of required datapacks
        required_patterns = [
            "required datapack", 
            "datapack is required",
            "requires the datapack",
            "must install datapack",
            "datapack must be installed"
        ]
        
        if any(pattern in description for pattern in required_patterns):
            # If we have explicit mentions, look for the name of the datapack
            # Further processing could be done here in the future
            print(f"Found strong evidence of required datapack for {mod_name}, but no specific datapack ID")
        
        return datapack_ids
    
    def _resolve_modrinth_dependency(self, dependency, minecraft_version, loader):
        """
        Resolve a dependency from Modrinth.
        
        Args:
            dependency (dict): Dependency data from Modrinth
            minecraft_version (str): Minecraft version
            loader (str): Mod loader (fabric, forge)
            
        Returns:
            dict: Resolved dependency data
        """
        # Skip optional dependencies
        if dependency.get('dependency_type') == 'optional':
            return None
        
        project_id = dependency.get('project_id')
        if not project_id:
            print(f"Warning: Dependency missing project_id: {dependency}")
            return None
        
        # Get mod details
        mod = self.modrinth_api.get_mod(project_id)
        if not mod:
            print(f"Warning: Could not find dependency mod: {project_id}")
            return None
        
        # Get versions compatible with minecraft version and loader
        versions = self.modrinth_api.get_mod_versions(project_id, minecraft_version, loader)
        if not versions:
            print(f"Warning: No compatible versions found for dependency {mod.get('title')} ({project_id})")
            return None
        
        # Use the newest compatible version
        version = versions[0]
        
        # Create dependency entry
        return {
            "name": mod.get('title'),
            "id": project_id,
            "version": version.get('id'),
            "source": "modrinth",
            "required_by": []  # Will be filled in later
        }
    
    def _resolve_curseforge_dependency(self, dependency, minecraft_version, loader):
        """
        Resolve a dependency from CurseForge.
        
        Args:
            dependency (dict): Dependency data from CurseForge
            minecraft_version (str): Minecraft version
            loader (str): Mod loader (fabric, forge)
            
        Returns:
            dict: Resolved dependency data
        """
        # Skip optional dependencies (type 3)
        if dependency.get('relationType') == 3:
            return None
        
        mod_id = dependency.get('modId')
        if not mod_id:
            print(f"Warning: Dependency missing modId: {dependency}")
            return None
        
        # Get mod details
        mod = self.curseforge_api.get_mod(mod_id)
        if not mod:
            print(f"Warning: Could not find dependency mod: {mod_id}")
            return None
        
        # Get files compatible with minecraft version and loader
        files = self.curseforge_api.get_mod_files(mod_id, minecraft_version, loader)
        if not files:
            print(f"Warning: No compatible files found for dependency {mod.get('name')} ({mod_id})")
            return None
        
        # Use the newest compatible file
        file = files[0]
        
        # Create dependency entry
        return {
            "name": mod.get('name'),
            "id": mod_id,
            "version": file.get('id'),
            "source": "curseforge",
            "required_by": []  # Will be filled in later
        }
    
    def resolve_dependencies(self, profile):
        """
        Resolve all dependencies for mods in a profile.
        
        Args:
            profile (dict): Profile data with mods list
            
        Returns:
            dict: Updated profile with resolved dependencies
        """
        if not profile:
            print("Error: Invalid profile")
            return profile
        
        minecraft_version = profile.get('minecraft_version')
        loader = profile.get('loader')
        mods = profile.get('mods', [])
        
        if not minecraft_version or not loader or not mods:
            print("Error: Profile missing required fields")
            return profile
        
        print(f"Resolving dependencies for profile {profile.get('name')}")
        
        # Create a dictionary for tracking dependencies
        dependency_map = {}
        
        # Create a set to track datapacks
        datapack_identifiers = set()
        
        # Queue for BFS dependency traversal
        queue = deque()
        
        # Add all mods to the queue
        for mod in mods:
            queue.append((mod, None))
        
        # Process the queue
        while queue:
            current_mod, parent_id = queue.popleft()
            mod_id = current_mod.get('id')
            mod_source = current_mod.get('source', '').lower()
            
            # Skip if mod has no ID or source
            if not mod_id or not mod_source:
                continue
            
            # If this is a dependency, add the parent to required_by
            if parent_id and mod_id in dependency_map:
                if parent_id not in dependency_map[mod_id]['required_by']:
                    dependency_map[mod_id]['required_by'].append(parent_id)
                continue
            
            # Get mod details to check for datapack dependencies
            mod_details = None
            file_info = None
            
            if mod_source == 'modrinth':
                mod_details = self.modrinth_api.get_mod(mod_id)
                # Get specific file info if available
                version_id = current_mod.get('version')
                if version_id:
                    versions = self.modrinth_api.get_mod_versions(mod_id)
                    for version in versions:
                        if version.get('id') == version_id:
                            file_info = version
                            break
            elif mod_source == 'curseforge':
                mod_details = self.curseforge_api.get_mod(mod_id)
                # Get specific file info if available
                file_id = current_mod.get('version')
                if file_id:
                    try:
                        file_id = int(file_id)
                        files = self.curseforge_api.get_mod_files(mod_id)
                        for file in files:
                            if file.get('id') == file_id:
                                file_info = file
                                break
                    except ValueError:
                        print(f"Warning: Invalid file ID for CurseForge mod: {file_id}")
            
            # Extract potential datapack identifiers
            if mod_details:
                potential_datapacks = self._extract_datapack_identifiers(mod_details, mod_source, file_info)
                for datapack_id in potential_datapacks:
                    datapack_identifiers.add((datapack_id, mod_source))
            
            # Get dependencies based on the source
            dependencies = []
            if mod_source == 'modrinth':
                version_id = current_mod.get('version')
                if version_id:
                    # Get versions to find dependencies
                    versions = self.modrinth_api.get_mod_versions(mod_id)
                    for version in versions:
                        if version.get('id') == version_id:
                            dependencies = version.get('dependencies', [])
                            break
                            
            elif mod_source == 'curseforge':
                file_id = current_mod.get('version')
                if file_id:
                    try:
                        file_id = int(file_id)
                        dependencies = self.curseforge_api.get_mod_dependencies(mod_id, file_id)
                    except ValueError:
                        print(f"Warning: Invalid file ID for CurseForge mod: {file_id}")
            
            # Process dependencies
            for dep in dependencies:
                resolved_dep = None
                
                if mod_source == 'modrinth':
                    resolved_dep = self._resolve_modrinth_dependency(dep, minecraft_version, loader)
                elif mod_source == 'curseforge':
                    resolved_dep = self._resolve_curseforge_dependency(dep, minecraft_version, loader)
                
                if resolved_dep:
                    dep_id = resolved_dep.get('id')
                    
                    # Add parent to required_by
                    if mod_id not in resolved_dep['required_by']:
                        resolved_dep['required_by'].append(mod_id)
                    
                    # Add or update dependency in map
                    if dep_id not in dependency_map:
                        dependency_map[dep_id] = resolved_dep
                        # Add to queue for further dependency resolution
                        queue.append((resolved_dep, mod_id))
                    else:
                        # Update required_by
                        if mod_id not in dependency_map[dep_id]['required_by']:
                            dependency_map[dep_id]['required_by'].append(mod_id)
        
        # Convert dependency map to list
        dependencies = list(dependency_map.values())
        
        # Update profile with dependencies
        profile['dependencies'] = dependencies
        
        print(f"Found {len(dependencies)} dependencies")
        for dep in dependencies:
            required_by = ', '.join(dep.get('required_by', []))
            print(f"  {dep.get('name')} - Required by: {required_by}")
        
        # Add datapacks to profile if they're not already there
        if datapack_identifiers:
            print(f"Found {len(datapack_identifiers)} potential datapack dependencies")
            
            # Ensure datapacks field exists
            if 'datapacks' not in profile:
                profile['datapacks'] = []
            
            # Get existing datapack IDs
            existing_datapack_ids = {dp.get('id') for dp in profile.get('datapacks', [])}
            
            # Filter to only include new datapacks
            new_datapacks = [(dp_id, source) for dp_id, source in datapack_identifiers 
                            if dp_id not in existing_datapack_ids]
            
            if new_datapacks:
                print(f"Adding {len(new_datapacks)} new datapacks to profile")
                
                # Check for each datapack across both sources if the current one fails
                from core.mod_search import ModSearch
                mod_search = ModSearch()
                
                # Cache to prevent redundant API calls
                datapack_details_cache = {}
                
                for datapack_id, preferred_source in new_datapacks:
                    print(f"Processing datapack: {datapack_id}")
                    
                    # Skip datapack if we've already tried and failed
                    if datapack_id in datapack_details_cache and datapack_details_cache[datapack_id] is None:
                        print(f"  Note: Already tried and failed to find datapack: {datapack_id} - skipping")
                        continue
                    
                    # Try both sources if needed, with preferred source first
                    datapack_entry = None
                    sources_to_try = [preferred_source]
                    if preferred_source == 'modrinth':
                        sources_to_try.append('curseforge')
                    elif preferred_source == 'curseforge':
                        sources_to_try.append('modrinth')
                    
                    for source in sources_to_try:
                        # Check cache first
                        cache_key = f"{datapack_id}_{source}"
                        if cache_key in datapack_details_cache:
                            datapack_details = datapack_details_cache[cache_key]
                            if datapack_details is None:
                                # We already tried this and failed
                                continue
                        else:
                            # Not in cache, make the API call
                            try:
                                datapack_details = mod_search.get_mod_details(datapack_id, source)
                                # Cache the result, even if it's None
                                datapack_details_cache[cache_key] = datapack_details
                                if datapack_details is None:
                                    continue
                            except Exception as e:
                                print(f"  Warning: Error checking datapack {datapack_id} from {source}: {e}")
                                # Cache the failure
                                datapack_details_cache[cache_key] = None
                                continue
                        
                        # Get versions if we have valid details
                        if datapack_details:
                            try:
                                versions = mod_search.get_mod_versions(
                                    datapack_id, 
                                    source, 
                                    minecraft_version
                                )
                                
                                if versions:
                                    # Use the newest compatible version
                                    version = versions[0]
                                    
                                    # Create datapack entry
                                    datapack_entry = {
                                        "name": datapack_details.get('name'),
                                        "id": datapack_id,
                                        "version": version.get('id'),
                                        "source": source.lower()
                                    }
                                    
                                    # Add to profile
                                    profile['datapacks'].append(datapack_entry)
                                    print(f"  Added datapack: {datapack_details.get('name')}")
                                    break
                                else:
                                    print(f"  Note: No compatible versions found for datapack {datapack_id}")
                            except Exception as e:
                                print(f"  Warning: Error getting versions for datapack {datapack_id} from {source}: {e}")
                    
                    # If the datapack wasn't found, mark it in the cache to avoid future lookups
                    if not datapack_entry:
                        print(f"  Note: Could not find datapack: {datapack_id} - skipping")
                        datapack_details_cache[datapack_id] = None
        
        return profile
    
    def check_compatibility(self, profile):
        """
        Check compatibility between mods and their dependencies.
        
        Args:
            profile (dict): Profile data with mods and dependencies
            
        Returns:
            list: List of compatibility issues
        """
        minecraft_version = profile.get('minecraft_version')
        loader = profile.get('loader')
        mods = profile.get('mods', [])
        dependencies = profile.get('dependencies', [])
        
        issues = []
        
        # Check each mod's compatibility with Minecraft version and loader
        all_mods = mods + dependencies
        for mod in all_mods:
            mod_id = mod.get('id')
            source = mod.get('source', '').lower()
            
            if source == 'modrinth':
                # Check if version is compatible
                versions = self.modrinth_api.get_mod_versions(mod_id, minecraft_version, loader)
                if not versions:
                    issues.append(f"Mod {mod.get('name')} ({mod_id}) is not compatible with Minecraft {minecraft_version} and {loader}")
            
            elif source == 'curseforge':
                # Check if version is compatible
                files = self.curseforge_api.get_mod_files(mod_id, minecraft_version, loader)
                if not files:
                    issues.append(f"Mod {mod.get('name')} ({mod_id}) is not compatible with Minecraft {minecraft_version} and {loader}")
        
        return issues

def main():
    """Test dependency resolution functionality."""
    from profile_manager import load_profile, save_profile
    
    resolver = DependencyResolver()
    
    # Example profile creation for testing
    profile = {
        "name": "test_dependency_profile",
        "minecraft_version": "1.20.1",
        "loader": "fabric",
        "mods": [
            {
                "name": "Create",
                "id": "create-fabric",
                "version": "0.5.1-d",
                "source": "modrinth"
            }
        ]
    }
    
    # Resolve dependencies
    updated_profile = resolver.resolve_dependencies(profile)
    
    # Check compatibility
    issues = resolver.check_compatibility(updated_profile)
    if issues:
        print("\nCompatibility issues:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\nNo compatibility issues found")
    
if __name__ == '__main__':
    main() 