# Docker Integration

## Docker Desktop Requirements

- Docker Desktop installed locally
- Docker Compose support
- Local volume mounting capability

## Minecraft Server Docker Image Structure

Base image: `itzg/minecraft-server`

Environment variables:
- `TYPE`: Server type (VANILLA, FORGE, FABRIC)
- `VERSION`: Minecraft version
- `EULA`: "TRUE" (required to accept Minecraft EULA)
- `FORGE_VERSION`: Forge version if using Forge
- `FABRIC_VERSION`: Fabric version if using Fabric
- `MEMORY`: Memory allocation (e.g., "4G")

Volumes:
- `/data`: Server data directory
- `/mods`: Mods directory (copied from local cache)
- `/config`: Config files
- `/world`: World data

## Docker Compose Template

```yaml
version: '3'

services:
  minecraft:
    image: itzg/minecraft-server:latest
    container_name: minecraft_${PROFILE_NAME}
    environment:
      TYPE: ${SERVER_TYPE}
      VERSION: ${MC_VERSION}
      EULA: "TRUE"
      FORGE_VERSION: ${FORGE_VERSION}
      FABRIC_VERSION: ${FABRIC_VERSION}
      MEMORY: "4G"
    ports:
      - "25565:25565"
    volumes:
      - ./data:/data
      - ./mods:/mods:ro
      - ./config:/config
    restart: unless-stopped
```

## Docker Image Build Process

1. Create a new image with the base `itzg/minecraft-server`
2. Copy the mods from the local cache to the `/mods` directory
3. Set environment variables for Minecraft version and loader version
4. Build and tag the image with the profile name

## Testing Server with Docker

1. Start the container with proper environment variables
2. Monitor server logs for startup errors
3. Check for mod compatibility issues
4. Stop the container when testing is complete

## Dependency Resolution through Docker

1. Start server with current mod set
2. Parse logs for dependency errors
3. Identify missing or incompatible mods
4. Update modpack configuration
5. Rebuild and retest

## Docker Image Manager Script Functions

- `build_image`: Build a Docker image for a modpack profile
- `test_server`: Start a test server and analyze logs
- `extract_dependency_errors`: Parse server logs for dependency issues
- `cleanup_containers`: Remove test containers
- `update_docker_compose`: Generate docker-compose.yml for a profile 