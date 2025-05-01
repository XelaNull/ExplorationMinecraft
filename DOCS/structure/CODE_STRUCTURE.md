# Code Structure

This document explains the structure and organization of the Minecraft Modpack Manager codebase.

## Directory Structure

```
modpack_manager/
├── client_packs/            # Generated client-side modpacks (zip files)
├── modpack_cache/           # Downloaded mod files organized by MC version and loader
│   ├── 1.20.1/
│   │   ├── fabric/
│   │   └── forge/
│   └── ...
├── modpack_profiles/        # JSON profile configurations
├── scripts/                 # Main executable scripts
│   ├── modpack_manager.sh   # Primary management script
│   ├── docker_image_manager.sh  # Docker image creation and management
│   └── lib/                 # Supporting Python and shell scripts
│       ├── api/             # API interaction modules
│       │   ├── modrinth.py  # Modrinth API client
│       │   └── curseforge.py # CurseForge API client
│       ├── core/            # Core functionality
│       │   ├── dependency_resolver.py # Handles mod dependencies
│       │   ├── downloader.py # Downloads mods from APIs
│       │   ├── profile_manager.py # Manages modpack profiles
│       │   └── compatibility_checker.py # Checks version compatibilities
│       └── utils/           # Utility functions
│           ├── config.py    # Configuration handling
│           ├── logger.py    # Logging utilities
│           └── file_utils.py # File operations
└── backups/                 # Server world backups
```

## Core Components

### Shell Scripts

1. **modpack_manager.sh**
   - Main entry point for user commands
   - Parses command-line arguments
   - Dispatches to appropriate Python modules
   - Provides user-friendly CLI interface

2. **docker_image_manager.sh**
   - Handles Docker image creation and management
   - Builds Docker images with specified mods
   - Manages containers for testing and deployment
   - Analyzes server logs for compatibility issues

### Python Modules

#### API Clients

1. **modrinth.py**
   - Interfaces with Modrinth API
   - Searches for mods
   - Retrieves mod details and versions
   - Gets download URLs

2. **curseforge.py**
   - Interfaces with CurseForge API
   - Searches for mods
   - Retrieves mod details and versions
   - Gets download URLs

#### Core Functionality

1. **dependency_resolver.py**
   - Analyzes mod dependencies
   - Builds dependency graph
   - Resolves dependency conflicts
   - Determines required dependencies

2. **downloader.py**
   - Downloads mods from APIs
   - Manages download cache
   - Verifies downloaded files
   - Handles download errors and retries

3. **profile_manager.py**
   - Creates and manages modpack profiles
   - Reads and writes profile JSON files
   - Validates profile contents
   - Tracks dependencies

4. **compatibility_checker.py**
   - Determines compatible Minecraft versions
   - Checks mod compatibility with loaders
   - Analyzes server logs for errors
   - Suggests compatible version combinations

#### Utilities

1. **config.py**
   - Manages global configuration
   - Loads environment variables
   - Sets up API keys and credentials
   - Configures paths and defaults

2. **logger.py**
   - Handles logging across the application
   - Configures log levels and formats
   - Writes logs to files
   - Provides debug information

3. **file_utils.py**
   - Handles file operations
   - Creates and extracts ZIP archives
   - Manages cache directories
   - Handles file permissions

## Data Structures

### Modpack Profile (JSON)

```json
{
  "name": "profile_name",
  "minecraft_version": "1.20.1",
  "loader": "fabric",
  "loader_version": "0.14.21",
  "description": "A description of the modpack",
  "mods": [
    {
      "name": "Mod Name",
      "id": "mod-id",
      "version": "1.2.3",
      "source": "modrinth|curseforge",
      "required": true
    }
  ],
  "dependencies": [
    {
      "name": "Dependency Name",
      "id": "dependency-id",
      "version": "1.2.3",
      "source": "modrinth|curseforge",
      "required_by": ["mod-id"]
    }
  ]
}
```

### Docker Compose (YAML)

```yaml
version: '3'
services:
  minecraft:
    image: minecraft_profile_name
    container_name: minecraft_profile_name
    environment:
      TYPE: "FABRIC|FORGE"
      VERSION: "1.20.1"
      EULA: "TRUE"
      FABRIC_VERSION: "0.14.21"
      MEMORY: "4G"
    ports:
      - "25565:25565"
    volumes:
      - ./data:/data
    restart: unless-stopped
```

## Workflow and Interactions

1. User invokes `modpack_manager.sh` with commands
2. Shell script parses arguments and calls Python modules
3. Python modules interact with APIs, file system, and Docker
4. Results are returned to shell script
5. Shell script presents information to user 