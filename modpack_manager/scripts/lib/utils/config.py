#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration module for Minecraft Modpack Manager.
Handles loading and management of configuration settings.
Compatible with Python 2.7 and 3+.
"""

from __future__ import print_function, division, unicode_literals
import os
import sys
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Python 2/3 compatibility
PY2 = sys.version_info[0] == 2
if PY2:
    from io import open

# Base directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')
PROFILES_DIR = os.path.join(BASE_DIR, 'modpack_profiles')
CACHE_DIR = os.path.join(BASE_DIR, 'modpack_cache')
CLIENT_PACKS_DIR = os.path.join(BASE_DIR, 'client_packs')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure directories exist
for directory in [PROFILES_DIR, CACHE_DIR, CLIENT_PACKS_DIR, LOGS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# API configuration
# These values should be overridden from the config file if it exists
MODRINTH_API = "https://api.modrinth.com/v2"
MODRINTH_API_KEY = "mrp_wsVIgH747NJ7zaACF3o27LXKO6Ovr9PnowcDjW4rkYl07SFTPmCR40LXfVj7"
CURSEFORGE_API = "https://api.curseforge.com"
CURSEFORGE_API_KEY = "$2a$10$Ml/ijVvjaWaNiQetMHMqrevxRhu2OTUSbTe0/BPBPXizUGu83SSJa"
USER_AGENT = "MinecraftModDownloader/1.0"
MINECRAFT_GAME_ID = 432
MC_MODS_CLASS_ID = 6

# Attempt to load config from file
config_path = os.path.join(SCRIPTS_DIR, 'config.json')
config = {}

def load_config():
    """Load configuration from file."""
    global MODRINTH_API, MODRINTH_API_KEY, CURSEFORGE_API, CURSEFORGE_API_KEY
    global USER_AGENT, MINECRAFT_GAME_ID, MC_MODS_CLASS_ID
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Update global variables with values from config file
            MODRINTH_API = config.get('modrinth_api', MODRINTH_API)
            MODRINTH_API_KEY = config.get('modrinth_api_key', MODRINTH_API_KEY)
            CURSEFORGE_API = config.get('curseforge_api', CURSEFORGE_API)
            CURSEFORGE_API_KEY = config.get('curseforge_api_key', CURSEFORGE_API_KEY)
            USER_AGENT = config.get('user_agent', USER_AGENT)
            MINECRAFT_GAME_ID = config.get('minecraft_game_id', MINECRAFT_GAME_ID)
            MC_MODS_CLASS_ID = config.get('mc_mods_class_id', MC_MODS_CLASS_ID)
            
            logger.info("Configuration loaded from %s", config_path)
        except Exception as e:
            logger.error("Error loading configuration: %s", e)

# Call this at import time
load_config()

def get_profile_path(profile_name):
    """
    Get the path to a profile JSON file.
    
    Args:
        profile_name (str): Profile name
        
    Returns:
        str: Path to profile JSON file
    """
    return os.path.join(PROFILES_DIR, f"{profile_name}.json")

def get_profiles_dir():
    """
    Get the path to profiles directory.
    
    Returns:
        str: Path to profiles directory
    """
    return PROFILES_DIR

def get_cache_dir(minecraft_version, loader):
    """
    Get the path to a cache directory for a specific Minecraft version and loader.
    
    Args:
        minecraft_version (str): Minecraft version
        loader (str): Mod loader (fabric, forge)
        
    Returns:
        str: Path to cache directory
    """
    cache_dir = os.path.join(CACHE_DIR, minecraft_version, loader.lower())
    
    # Ensure directory exists
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
        
    return cache_dir

def get_client_packs_dir():
    """
    Get the path to client packs directory.
    
    Returns:
        str: Path to client packs directory
    """
    return CLIENT_PACKS_DIR

def get_datapack_cache_path(minecraft_version):
    """
    Get the path to the data pack cache directory for a specific Minecraft version.
    
    Args:
        minecraft_version (str): Minecraft version
        
    Returns:
        str: Data pack cache directory path
    """
    return os.path.join(CACHE_DIR, minecraft_version, 'datapacks')

def get_client_pack_path(profile_name):
    """
    Get the path to a client pack ZIP file.
    
    Args:
        profile_name (str): Profile name
        
    Returns:
        str: Client pack file path
    """
    return os.path.join(CLIENT_PACKS_DIR, f"{profile_name}.zip")

def get_backup_path(profile_name):
    """
    Get the path to a backup directory for a profile.
    
    Args:
        profile_name (str): Profile name
        
    Returns:
        str: Backup directory path
    """
    return os.path.join(LOGS_DIR, profile_name)

if __name__ == '__main__':
    """Test configuration functionality."""
    print("Project root:", BASE_DIR)
    print("Profiles directory:", get_profiles_dir())
    print("Profile path:", get_profile_path("test_profile"))
    print("Mod cache path:", get_cache_dir("1.20.1", "fabric"))
    print("Datapack cache path:", get_datapack_cache_path("1.20.1"))
    print("Client pack path:", get_client_pack_path("test_profile"))
    print("Backup path:", get_backup_path("test_profile"))
    
    print("\nConfiguration:")
    for key, value in config.items():
        print(f"{key}: {value}") 