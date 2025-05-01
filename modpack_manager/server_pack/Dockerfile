FROM itzg/minecraft-server:latest

# Set environment variables for the Minecraft server
ENV TYPE=DOCKER
ENV EULA=TRUE
ENV VERSION=1.20.1
ENV TYPE=FORGE
ENV FORGE_VERSION=47.3.0

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

# Label with modpack details
LABEL modpack.name="exploration_modpack" \
      modpack.minecraft_version="1.20.1" \
      modpack.loader="forge" \
      modpack.loader_version="47.3.0" \
      modpack.build_date="Wed Apr 30 20:02:15 EDT 2025"
