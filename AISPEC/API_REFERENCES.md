# API References

## Modrinth API

- **Base URL**: `https://api.modrinth.com/v2`
- **API Key**: Environment variable `MODRINTH_API_KEY`
- **User Agent**: Required in headers as `User-Agent: MinecraftModDownloader/1.0`

### Key Endpoints

#### Search Mods
`GET /search`

Parameters:
- `query` (string): Search query
- `facets` (string): JSON-encoded array of filter arrays
- `index` (string): One of "relevance", "downloads", "follows", "newest", "updated"
- `limit` (integer): Maximum number of results (default: 10)

Example facets:
```json
[["categories:forge"],["versions:1.20.1"]]
```

#### Get Mod
`GET /project/{id}`

Parameters:
- `id` (string): Mod ID or slug

#### Get Mod Versions
`GET /project/{id}/version`

Parameters:
- `id` (string): Mod ID or slug
- `loaders` (array): Game loaders (e.g., "fabric", "forge")
- `game_versions` (array): Game versions (e.g., "1.20.1")

#### Download URL
`GET /version/{id}/download`

Parameters:
- `id` (string): Version ID

## CurseForge API

- **Base URL**: `https://api.curseforge.com`
- **API Key**: Required in headers as `x-api-key: $CURSEFORGE_API_KEY`
- **Game ID for Minecraft**: 432
- **Class ID for Minecraft Mods**: 6

### Key Endpoints

#### Search Mods
`GET /v1/mods/search`

Parameters:
- `gameId` (integer): 432 for Minecraft
- `classId` (integer): 6 for Mods
- `searchFilter` (string): Text search
- `gameVersion` (string): Minecraft version
- `modLoaderType` (integer): 1 for Forge, 4 for Fabric
- `sortField` (integer): Sort method (e.g., 1 for featured, 2 for popularity)
- `sortOrder` (string): "asc" or "desc"

#### Get Mod
`GET /v1/mods/{modId}`

Parameters:
- `modId` (integer): Mod ID

#### Get Mod Files
`GET /v1/mods/{modId}/files`

Parameters:
- `modId` (integer): Mod ID
- `gameVersion` (string): Minecraft version
- `modLoaderType` (integer): 1 for Forge, 4 for Fabric

#### Download URL
The file download URL is provided in the file object response as `downloadUrl`

## Dependency Resolution

When resolving dependencies:
1. Get the mod's dependencies from its metadata
2. For each dependency, check if it's compatible with the current Minecraft and loader versions
3. If not already in the modpack, add it to a queue for processing
4. Process the queue recursively until all dependencies are resolved

## Version Compatibility

When determining compatible versions:
1. Start with the highest compatible Minecraft version
2. For each mod, find the newest version supporting that Minecraft version
3. If no compatible version exists, try the next highest Minecraft version
4. Once Minecraft version is determined, follow the same process for loader versions 