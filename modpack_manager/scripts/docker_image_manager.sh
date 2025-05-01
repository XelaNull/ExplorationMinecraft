#!/bin/bash
# Docker Image Manager for Minecraft Modpack Manager
# Handles creation of Docker images for Minecraft servers

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$ROOT_DIR")"

# Set up Python environment
source "$SCRIPT_DIR/export_pythonpath.sh" > /dev/null

# Default values
DOCKERFILE="$ROOT_DIR/server_pack/Dockerfile"
SERVER_PACK_DIR="$ROOT_DIR/server_pack"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

function usage() {
    echo "Usage: $0 [command] [profile_name] [options]"
    echo ""
    echo "Commands:"
    echo "  build [profile_name]    Build a Docker image for a modpack profile"
    echo "  start                   Start the Docker container using docker-compose"
    echo "  stop                    Stop the Docker container"
    echo "  restart                 Restart the Docker container"
    echo "  logs                    View the Docker container logs"
    echo "  push [profile_name]     Push a Docker image to a registry"
    echo "  help                    Display this help message"
    echo ""
    echo "Options:"
    echo "  --tag [tag]             Tag for the Docker image (default: profile_name:latest)"
    echo "  --registry [url]        Registry URL for push command"
    echo "  --verbose               Show verbose output"
    echo ""
    echo "Examples:"
    echo "  $0 build exploration_modpack"
    echo "  $0 start"
    echo "  $0 stop"
    echo "  $0 push exploration_modpack --registry myregistry.com --tag 1.0.0"
}

function build_image() {
    local profile_name=$1
    local tag=${2:-"minecraft-$profile_name:latest"}
    local verbose=$3
    
    if [ -z "$profile_name" ]; then
        echo "Error: Profile name required."
        usage
        exit 1
    fi
    
    echo "Building Docker image for profile: $profile_name"
    echo "==========================================================="
    
    # Check if server pack exists
    if [ ! -d "$SERVER_PACK_DIR" ]; then
        echo "Error: Server pack directory does not exist: $SERVER_PACK_DIR"
        echo "Please run ./modpack_manager.sh create-server-pack --profile $profile_name first."
        exit 1
    fi
    
    # Create Dockerfile
    echo "Creating Dockerfile at $DOCKERFILE..."
    
    # Get profile details for Docker image configuration
    local profile_file="$ROOT_DIR/modpack_profiles/$profile_name.json"
    
    if [ ! -f "$profile_file" ]; then
        echo "Error: Profile file not found: $profile_file"
        exit 1
    fi
    
    # Extract Minecraft version and mod loader from profile
    local mc_version=$(grep -o '"minecraft_version": *"[^"]*"' "$profile_file" | cut -d'"' -f4)
    local loader=$(grep -o '"loader": *"[^"]*"' "$profile_file" | cut -d'"' -f4)
    local loader_version=$(grep -o '"loader_version": *"[^"]*"' "$profile_file" | cut -d'"' -f4)
    
    echo "Profile details: Minecraft $mc_version with $loader $loader_version"
    
    # Create base Dockerfile
    cat > "$DOCKERFILE" << EOF
FROM itzg/minecraft-server:latest

# Set environment variables for the Minecraft server
ENV TYPE=DOCKER
ENV EULA=TRUE
ENV VERSION=$mc_version
EOF

    # Add loader-specific environment variables
    if [ "$loader" == "forge" ]; then
        echo "ENV TYPE=FORGE" >> "$DOCKERFILE"
        echo "ENV FORGE_VERSION=$loader_version" >> "$DOCKERFILE"
    elif [ "$loader" == "fabric" ]; then
        echo "ENV TYPE=FABRIC" >> "$DOCKERFILE"
        echo "ENV FABRIC_VERSION=$loader_version" >> "$DOCKERFILE"
    else
        echo "Error: Unsupported loader: $loader"
        exit 1
    fi
    
    # Complete the Dockerfile with modpack-specific content
    echo "Adding modpack-specific configuration to Dockerfile..."
    
    # Add volume configuration for data persistence
    cat >> "$DOCKERFILE" << EOF

# Copy the modpack files
COPY --chown=1000:1000 mods /data/mods
COPY --chown=1000:1000 config /data/config
COPY --chown=1000:1000 datapacks /data/world/datapacks
COPY --chown=1000:1000 server.properties /data/server.properties
COPY --chown=1000:1000 ops.json /data/ops.json
COPY --chown=1000:1000 whitelist.json /data/whitelist.json

EOF

    # Add server icon if it exists
    if [ -f "$SERVER_PACK_DIR/server-icon.png" ]; then
        cat >> "$DOCKERFILE" << EOF
# Set server icon
COPY --chown=1000:1000 server-icon.png /data/server-icon.png
EOF
    fi

    # Continue with the rest of the Dockerfile
    cat >> "$DOCKERFILE" << EOF
# Set user for better security
USER 1000

VOLUME ["/data"]

# Label with modpack details
LABEL modpack.name="$profile_name" \\
      modpack.minecraft_version="$mc_version" \\
      modpack.loader="$loader" \\
      modpack.loader_version="$loader_version" \\
      modpack.build_date="$(date)"
EOF
    
    # Show Dockerfile for debugging
    if [ "$verbose" = true ]; then
        echo "====== Dockerfile Contents ======"
        cat "$DOCKERFILE"
        echo "==============================="
    fi
    
    # Count mods for progress indicator
    local mod_count=$(ls -1 "$SERVER_PACK_DIR/mods" 2>/dev/null | wc -l | tr -d ' ')
    echo "Server pack contains $mod_count mods"

    # Build the Docker image with docker-compose
    echo "Building Docker image with docker-compose"
    echo "This may take several minutes depending on your system..."
    echo "==========================================================="
    
    # Change to the project root directory before building
    cd "$PROJECT_ROOT"
    
    # Use --no-cache for more consistent builds
    if [ "$verbose" = true ]; then
        # More verbose output
        docker-compose build --no-cache
    else
        # Standard progress 
        docker-compose build
    fi
    
    # Check build result
    if [ $? -eq 0 ]; then
        echo "==========================================================="
        echo "Docker image built successfully"
        echo "You can now start the server with: $0 start"
    else
        echo "==========================================================="
        echo "Error: Docker build failed."
        echo "Please check the error messages above."
        exit 1
    fi
}

function check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo "Error: docker-compose.yml not found at $COMPOSE_FILE"
        exit 1
    fi
}

function start_container() {
    echo "Starting Minecraft server container..."
    check_compose_file
    cd "$PROJECT_ROOT"
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo "Server started successfully."
        echo "Container name: exploration_modpack_server"
        echo "You can view logs with: $0 logs"
        
        # Wait a bit and show initial logs
        sleep 5
        docker-compose logs --tail=20
    else
        echo "Error: Failed to start the server."
        exit 1
    fi
}

function stop_container() {
    echo "Stopping Minecraft server container..."
    check_compose_file
    cd "$PROJECT_ROOT"
    docker-compose down
    
    if [ $? -eq 0 ]; then
        echo "Server stopped successfully."
    else
        echo "Error: Failed to stop the server."
        exit 1
    fi
}

function restart_container() {
    echo "Restarting Minecraft server container..."
    check_compose_file
    cd "$PROJECT_ROOT"
    docker-compose restart
    
    if [ $? -eq 0 ]; then
        echo "Server restarted successfully."
        # Show recent logs after restart
        sleep 5
        docker-compose logs --tail=20
    else
        echo "Error: Failed to restart the server."
        exit 1
    fi
}

function view_logs() {
    echo "Viewing Minecraft server logs..."
    check_compose_file
    cd "$PROJECT_ROOT"
    docker-compose logs -f
}

function push_image() {
    local profile_name=$1
    local registry=$2
    local tag=${3:-"minecraft-$profile_name:latest"}
    
    if [ -z "$profile_name" ]; then
        echo "Error: Profile name required."
        usage
        exit 1
    fi
    
    if [ -z "$registry" ]; then
        echo "Error: Registry URL required for push command."
        usage
        exit 1
    fi
    
    echo "Pushing Docker image for profile: $profile_name"
    check_compose_file
    
    # Get the image name from docker-compose
    local image_name=$(docker-compose config | grep 'image:' | awk '{print $2}')
    
    if [ -z "$image_name" ]; then
        echo "Error: Could not determine image name from docker-compose.yml"
        exit 1
    fi
    
    # Tag image for registry
    local registry_tag="$registry/$tag"
    docker tag "$image_name" "$registry_tag"
    
    # Push to registry
    echo "Pushing image to registry: $registry_tag"
    docker push "$registry_tag"
    
    echo "Docker image pushed successfully: $registry_tag"
}

# Main script execution
command=$1
shift

# Default values
verbose=false

case $command in
    build)
        profile_name=$1
        shift
        tag=""
        
        while [[ $# -gt 0 ]]; do
            case $1 in
                --tag)
                    tag=$2
                    shift 2
                    ;;
                --verbose)
                    verbose=true
                    shift
                    ;;
                *)
                    echo "Unknown option: $1"
                    usage
                    exit 1
                    ;;
            esac
        done
        
        build_image "$profile_name" "$tag" "$verbose"
        ;;
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container
        ;;
    logs)
        view_logs
        ;;
    push)
        profile_name=$1
        shift
        registry=""
        tag=""
        
        while [[ $# -gt 0 ]]; do
            case $1 in
                --registry)
                    registry=$2
                    shift 2
                    ;;
                --tag)
                    tag=$2
                    shift 2
                    ;;
                --verbose)
                    verbose=true
                    shift
                    ;;
                *)
                    echo "Unknown option: $1"
                    usage
                    exit 1
                    ;;
            esac
        done
        
        push_image "$profile_name" "$registry" "$tag"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo "Unknown command: $command"
        usage
        exit 1
        ;;
esac

exit 0 