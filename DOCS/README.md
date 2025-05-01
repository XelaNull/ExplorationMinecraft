Minecraft Modpack Manager

- Uses Python 2.7 but supports Python 3+ as well.
- Uses a multi-file/directory structure for the modpack manager, to keep files small

Features:
* Modpack Profiles
* Supports Fabric and Forge
* Manages Minecraft and Fabric/Forge versions via environmental variables
* Retains Modpack Manager cache separate Docker server; Copies Mods into Image at build time
* Support Searching and Downloading Mods from Modrinth and Curseforge
* Builds a matrix of details on each mod and its dependencies.
* Supports searching based on keywords, categories, game version, and fabric/forge version
* Automatically determines highest version of Minecraft and Forge/Fabric that the Modpack supports
* Automatic dependency and error resolution through use of local Docker Desktop to start up server and examine the server logs
* Automatically extracts mrpack files
* Handles datta packs
* Simple CLI for managing Modpacks
    - Create, Delete, Edit, Download, Install, Update (find newest versions for all components that work together),and List Modpack
    - Create/Delete Modpack Profile
    - Edit an existing Modpack Profile by adding/removing mods
    - Download all Mods for a Modpack Profile
    - Install a Modpack Profile into a Docker Image
    - Update a Modpack Profile by finding new versions of mods or Fabric/Forge versions and updating the Modpack Profile
    - List all Modpack Profiles
    - List all Mods in a Modpack Profile
* Two scripts:
    - modpack_manager.sh: Main script for managing modpacks
    - docker_image_manager.sh: Manages creation of Docker images for each modpack

Directory Structure:
modpack_manager/
    - client_packs/
        - profile_name.zip         # Client-side modpacks packaged as ZIP for distribution
    - server_pack/                 # Contains the currently active server modpack
        - mods/                    # Server-side mods and shared mods
        - config/                  # Server configuration files
        - datapacks/               # Minecraft datapacks
    - modpack_cache/               # Cache of downloaded mods
        - mc_version/
            - 1.20.1/
                - fabric/
                - forge/
    - modpack_profiles/            # JSON profiles containing modpack definitions
        - profile_name.json
    - scripts/
        - modpack_manager.sh       # Main CLI for managing modpacks
        - docker_image_manager.sh  # Manages Docker images for server deployment
        - README.md

docker-compose.yml                 # Docker composition for server deployment
.env                               # Environment variables for Docker
README.md                          # Project documentation

Purpose of Client and Server Packs:
* client_packs/ - Stores multiple ZIP files that contain client-side modpacks for distribution to players
* server_pack/ - Contains the currently active server modpack that will be copied into the Docker image at build time

Docker Workflow:
1. The modpack_manager.sh script is used to create and manage modpack profiles
2. When a profile is ready to be deployed, the create-server-pack command prepares the server_pack/ directory
3. The docker_image_manager.sh script then builds a Docker image that includes the contents of server_pack/
4. The Docker image can be deployed using docker-compose or other container orchestration tools

Tool Usage Flow:
1. Create a new Modpack Profile
2. Search for Mods in Modrinth and Curseforge using keywords, categories, game version, and fabric/forge version
3. Resolve dependencies and download mods into the cache
4. Create client packs for distribution to players
5. Create server pack for Docker deployment
6. Build and deploy Docker image for the Minecraft server

# DO NOT REMOVE THIS LINE. THESE ARE THE MODS I WANT: Apotheosis, Create, Chipped, Chisels & Bits, Supplementaries, Just Enough Items, Quark, Alex's Mobs, Relics, L_Ender's Cataclysm, Dungeons and Taverns, Iron's Spells n Spellbooks, Alex's Caves, Sawmill, Terramity
# Known Minecraft version these work with: 1.20.1
# Known Fabric version these work with: 47.30.0



# ================= CONFIGURATION (from mod_explorer.py) =================
# Modrinth API key
MODRINTH_API_KEY = "mrp_wsVIgH747NJ7zaACF3o27LXKO6Ovr9PnowcDjW4rkYl07SFTPmCR40LXfVj7"
# CurseForge API key
CURSEFORGE_API_KEY = "$2a$10$Ml/ijVvjaWaNiQetMHMqrevxRhu2OTUSbTe0/BPBPXizUGu83SSJa"
# Base URLs for APIs
MODRINTH_API = "https://api.modrinth.com/v2"
CURSEFORGE_API = "https://api.curseforge.com"
USER_AGENT = "MinecraftModDownloader/1.0"
# Game ID for Minecraft in CurseForge
MINECRAFT_GAME_ID = 432
# Class ID for Minecraft Mods in CurseForge
MC_MODS_CLASS_ID = 6