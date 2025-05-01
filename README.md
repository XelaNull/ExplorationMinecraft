# Minecraft Modpack Manager

A comprehensive tool for creating, managing, and deploying Minecraft modpacks with Docker integration.

## Features

- Create and manage modpack profiles with specific Minecraft, Fabric, and Forge versions
- Search and download mods from Modrinth and CurseForge
- Automatic dependency resolution
- Docker integration for server testing and deployment
- Client-side modpack generation
- Mod update checking and management

## Quick Start

1. Clone this repository
2. Ensure you have Python (2.7 or 3+) and Docker Desktop installed
3. Run `./modpack_manager.sh` to see available commands

## Directory Structure

- `modpack_manager/` - Main application directory
  - `client_packs/` - Generated client-side modpacks (multiple zip files, one per profile)
  - `server_pack/` - Uncompressed server files for the active modpack (copied to Docker container during build)
    - `mods/` - Server-side mod files
    - `config/` - Configuration files for mods
    - `datapacks/` - Data packs for world generation and gameplay
  - `modpack_cache/` - Downloaded mod files organized by Minecraft version and loader
  - `modpack_profiles/` - JSON profile configurations
  - `scripts/` - Main executable scripts
- `DOCS/` - Documentation
- `AISPEC/` - Technical reference documentation
- `DEVJOURNAL/` - Development progress records

## Server Deployment

The `server_pack/` directory contains the raw uncompressed files for the currently installed modpack. 
During the Docker image build process (via `docker_image_manager.sh`), this entire directory is copied 
into the Minecraft server container, making it ready to run with all mods, configs, and datapacks properly installed.

Unlike `client_packs/` which can store multiple modpack ZIP archives, the `server_pack/` directory represents 
only the currently active server configuration. When deploying a different modpack profile to the server, 
the contents of this directory will be replaced.

## Documentation

For detailed usage and implementation details, see the documentation:

- [Usage Guide](DOCS/usage/MANAGER_USAGE.md)
- [Server Management](DOCS/server/SERVER_MANAGEMENT.md)
- [Code Structure](DOCS/structure/CODE_STRUCTURE.md)

## Development

See the [Development Journal](DEVJOURNAL/) for progress updates and technical decisions.

## License

This project is open source and available under the MIT License.

## Acknowledgements

- Uses the [Modrinth API](https://docs.modrinth.com/api-spec/) and [CurseForge API](https://docs.curseforge.com/) for mod search and download
- Built on the excellent [itzg/minecraft-server](https://github.com/itzg/docker-minecraft-server) Docker image 