# Minecraft Server Management

This document explains how to set up, manage, and troubleshoot Minecraft servers using the modpack manager and Docker.

## Setting Up a New Server

### Prerequisites

- Docker Desktop installed and running
- A modpack profile already created and tested
- Sufficient RAM for server operation (minimum 4GB recommended)

### Deployment

To deploy a server using a modpack profile:

```bash
./modpack_manager.sh deploy --profile [profile_name]
```

This will:
1. Download all required mods if not already cached
2. Build a Docker image with the specified Minecraft and loader versions
3. Create a docker-compose.yml file for easy management
4. Start the server container

### Configuration

The server configuration is generated in the `servers/[profile_name]/data/[profile_name]/` directory:

- `server.properties`: Server configuration
- `ops.json`: Server operators
- `whitelist.json`: Whitelisted players

You can modify these files and restart the server to apply changes.

## Managing the Server

### Starting the Server

```bash
./modpack_manager.sh start --profile [profile_name]
```

### Stopping the Server

```bash
./modpack_manager.sh stop --profile [profile_name]
```

### Restarting the Server

```bash
./modpack_manager.sh restart --profile [profile_name]
```

### Checking Server Status

```bash
./modpack_manager.sh status --profile [profile_name]
```

### Viewing Server Logs

```bash
./modpack_manager.sh logs --profile [profile_name]
```

## Rebuilding and Updating

### Rebuilding the Server

If you need to rebuild the server from scratch:

```bash
# First, create a fresh server pack
./modpack_manager.sh create-server-pack --profile [profile_name] --force
# Then redeploy the server
./modpack_manager.sh deploy --profile [profile_name]
```

### Updating the Server

To update to newer mod versions:

1. Update your profile mods:
```bash
./modpack_manager.sh update --profile [profile_name]
```

2. Create a new server pack with the updated mods:
```bash
./modpack_manager.sh create-server-pack --profile [profile_name] --force
```

3. Redeploy the server:
```bash
./modpack_manager.sh deploy --profile [profile_name]
```

## Backing Up and Restoring

### Creating a World Backup

```bash
./modpack_manager.sh backup --profile [profile_name]
```

This creates a timestamped backup in `backups/[profile_name]/`.

### Restoring from Backup

```bash
./modpack_manager.sh restore --profile [profile_name] --backup [backup_name]
```

## Technical Details

### Docker Implementation

The server deployment uses:
- itzg/minecraft-server Docker image as the base image
- Docker Compose for service management
- Volume mounts for world data persistence

### Directory Structure

- `server_pack/`: Contains the mods, configs, and datapacks for the server
- `servers/[profile_name]/`: Contains the deployed server with docker-compose.yml
- `servers/[profile_name]/data/`: Contains persistent server data
- `backups/[profile_name]/`: Contains server backups

### Customizing Server Resources

To allocate more resources to the server, use:

```bash
./modpack_manager.sh deploy --profile [profile_name] --memory 6G
```

To use a different port:

```bash
./modpack_manager.sh deploy --profile [profile_name] --port 25566
```

### Building Images Manually

You can build Docker images manually with the docker_image_manager.sh script:

```bash
./scripts/docker_image_manager.sh build [profile_name]
```

For verbose output and troubleshooting:

```bash
./scripts/docker_image_manager.sh build [profile_name] --verbose
```

## Troubleshooting

### Server Crashes on Startup

1. Check the logs for mod compatibility issues:
   ```bash
   ./modpack_manager.sh logs --profile [profile_name]
   ```

2. Check that all datapacks are compatible with your Minecraft version and mods.

3. Ensure your system has enough resources:
   - At least 4GB of RAM allocated to the Docker container
   - Sufficient disk space for world generation

### Docker Build Issues

If the Docker image build process is taking too long or seems to hang:

1. Use the verbose option to see detailed output:
   ```bash
   ./scripts/docker_image_manager.sh build [profile_name] --verbose
   ```

2. Ensure Docker Desktop has enough resources allocated:
   - Open Docker Desktop Settings
   - Go to Resources and increase CPU/Memory limits

3. Check for network connectivity issues, as the build process needs to download the base image and Forge/Fabric installer.

### Out of Memory Errors

Increase the memory allocation:

```bash
./modpack_manager.sh deploy --profile [profile_name] --memory 8G
```

### Port Conflicts

If you see an error about the port being already in use, change the server port:

```bash
./modpack_manager.sh deploy --profile [profile_name] --port 25566
```

### Missing Dependencies

If mods are missing dependencies:

```bash
# Resolve dependencies and recreate the server pack
./modpack_manager.sh resolve-dependencies --profile [profile_name]
./modpack_manager.sh create-server-pack --profile [profile_name] --force
./modpack_manager.sh deploy --profile [profile_name]
``` 