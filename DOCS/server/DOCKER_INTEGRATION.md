# Docker Integration for Minecraft Modpack Manager

This document explains the technical details of how Docker integration works in the Minecraft Modpack Manager.

## Overview

The Minecraft Modpack Manager uses Docker to create isolated, reproducible Minecraft server environments. This makes it easy to:

- Deploy servers with consistent configurations
- Isolate server instances from each other
- Provide a standardized way to manage server resources
- Enable easy backup and restoration of server data

## Components

### Docker Image

The Docker image for each modpack is built using [itzg/minecraft-server](https://github.com/itzg/docker-minecraft-server) as the base image. This provides a robust foundation with:

- Java runtime environment
- Server startup scripts
- Health checks
- Memory management
- Support for different Minecraft server types (Vanilla, Forge, Fabric, etc.)

Our system adds:
- Mod files from the modpack profile
- Configuration files
- Datapacks
- Server settings (server.properties, ops.json, whitelist.json)

### Docker Compose

Each server deployment uses Docker Compose to:
- Define port mappings
- Set up volume mounting for persistent data
- Configure environment variables
- Enable container restart policies

## Workflow

1. **Building the Image**:
   - The `docker_image_manager.sh` script builds a custom Dockerfile
   - Files from the `server_pack/` directory are copied into the image
   - Environment variables are set based on the modpack profile (Minecraft version, loader type, etc.)

2. **Deploying a Server**:
   - The `server_management.py` script creates a docker-compose.yml file
   - A data directory is created for persistent server data
   - The server is started using Docker Compose

3. **Server Management**:
   - Start/stop/restart commands use Docker Compose
   - Logs are viewed through Docker Compose
   - Backups are created by copying data volumes to timestamped directories

## Technical Implementation

### Dockerfile Generation

The Dockerfile is generated dynamically based on the modpack profile:

```dockerfile
FROM itzg/minecraft-server:latest

# Set environment variables for the Minecraft server
ENV TYPE=FORGE  # or FABRIC depending on profile
ENV VERSION=1.20.1  # Minecraft version
ENV FORGE_VERSION=47.3.0  # Forge/Fabric version
ENV MEMORY=4G
ENV EULA=TRUE

# Copy the modpack files
COPY --chown=1000:1000 mods /data/mods
COPY --chown=1000:1000 config /data/config
COPY --chown=1000:1000 datapacks /data/world/datapacks
COPY --chown=1000:1000 server.properties /data/server.properties
COPY --chown=1000:1000 ops.json /data/ops.json
COPY --chown=1000:1000 whitelist.json /data/whitelist.json

# Set user for better security
USER 1000

VOLUME ["/data"]

# Labels for tracking
LABEL modpack.name="exploration_modpack"
      modpack.minecraft_version="1.20.1"
      modpack.loader="forge"
      modpack.loader_version="47.3.0"
      modpack.build_date="2025-04-27"
```

### Docker Compose File

The docker-compose.yml file is created for each server:

```yaml
services:
  minecraft:
    container_name: mc_{profile_name}
    image: minecraft-{profile_name}:latest
    ports:
      - "{server_port}:25565"
    environment:
      - MEMORY={memory}
      - EULA=TRUE
    volumes:
      - ./data/{profile_name}:/data
    restart: unless-stopped
```

## Security Considerations

- The container runs as a non-root user (UID 1000)
- Data volumes are properly permissioned
- Network ports are explicitly defined
- No unnecessary ports are exposed
- The container uses a dedicated volume for data persistence

## Resource Management

You can customize resource allocation when deploying a server:

```bash
./modpack_manager.sh deploy --profile [profile_name] --memory 8G --port 25566
```

This updates the Docker Compose configuration with your specified values.

## Advanced Usage

### Manual Image Building

For manual image building with detailed output:

```bash
./scripts/docker_image_manager.sh build [profile_name] --verbose
```

### Custom Base Images

To use a different base image, you would need to modify the `docker_image_manager.sh` script.

### Registry Integration

The `docker_image_manager.sh` script includes support for pushing images to a registry:

```bash
./scripts/docker_image_manager.sh push [profile_name] --registry [registry_url]
```

## Troubleshooting

### Common Docker Issues

1. **Insufficient Resources**:
   - Docker Desktop may need more RAM/CPU allocated
   - Check Docker Desktop settings under Resources

2. **Network Issues**:
   - Ensure Docker has network connectivity
   - Check if the port is already in use

3. **Volume Permission Issues**:
   - Server data volumes should be properly owned by UID 1000
   - Check if file permissions are correct in the server_pack directory

### Docker Logs

To view detailed Docker logs:

```bash
docker logs mc_{profile_name}
```

Or using our script:

```bash
./modpack_manager.sh logs --profile [profile_name]
```

## Future Improvements

- Add support for Docker networks for multi-server setups
- Implement Docker health checks for better monitoring
- Add resource usage metrics and monitoring
- Implement auto-scaling for busy servers 