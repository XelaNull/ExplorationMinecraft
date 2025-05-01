# Modpack Manager Usage Guide

This document describes how to use the Minecraft Modpack Manager to create, manage, and deploy modpacks.

## Prerequisites

- Python 2.7 or 3+ installed
- Docker Desktop installed for server testing
- Internet connection for downloading mods

## Command Structure

The modpack manager uses a simple command structure:

```bash
./modpack_manager.sh [command] [options]
```

## Available Commands

### Profile Management

#### Create a New Modpack Profile

```bash
./modpack_manager.sh create [profile_name] --minecraft [version] --loader [fabric|forge] --loader-version [version]
```

Example:
```bash
./modpack_manager.sh create exploration_pack --minecraft 1.20.1 --loader fabric --loader-version 0.14.21
```

#### Delete a Modpack Profile

```bash
./modpack_manager.sh delete [profile_name]
```

#### List All Modpack Profiles

```bash
./modpack_manager.sh list
```

#### Show Modpack Profile Details

```bash
./modpack_manager.sh show [profile_name]
```

### Mod Management

#### Search for Mods

```bash
./modpack_manager.sh search [search_terms] --profile [profile_name] --source [modrinth|curseforge|both]
```

Example:
```bash
./modpack_manager.sh search "Create mod" --profile exploration_pack --source both
```

#### Add a Mod to a Profile

```bash
./modpack_manager.sh add [mod_id] --profile [profile_name]
```

#### Remove a Mod from a Profile

```bash
./modpack_manager.sh remove [mod_id] --profile [profile_name]
```

#### List Mods in a Profile

```bash
./modpack_manager.sh list-mods --profile [profile_name]
```

### Package Management

#### Download All Mods for a Profile

```bash
./modpack_manager.sh download --profile [profile_name]
```

#### Create a Client Pack

```bash
./modpack_manager.sh package --profile [profile_name]
```

#### Check for Mod Updates

```bash
./modpack_manager.sh check-updates --profile [profile_name]
```

#### Update All Mods to Latest Compatible Versions

```bash
./modpack_manager.sh update --profile [profile_name]
```

### Server Management

#### Deploy Server to Docker

```bash
./modpack_manager.sh deploy --profile [profile_name]
```

#### Test Server Compatibility

```bash
./modpack_manager.sh test --profile [profile_name]
```

#### Check Server Status

```bash
./modpack_manager.sh status --profile [profile_name]
```

## Profile Files

Modpack profiles are stored in the `modpack_profiles/` directory as JSON files with the following structure:

```json
{
  "name": "exploration_pack",
  "minecraft_version": "1.20.1",
  "loader": "fabric",
  "loader_version": "0.14.21",
  "mods": [
    {
      "name": "Create",
      "id": "create-fabric",
      "version": "0.5.1-d",
      "source": "modrinth"
    },
    {
      "name": "Quark",
      "id": "308702",
      "version": "4.0.0",
      "source": "curseforge"
    }
  ],
  "dependencies": []
}
```

## Client Packs

Client packs are created as ZIP files in the `client_packs/` directory. These can be directly imported into the Minecraft launcher or MultiMC.

## Using Docker for Testing

The modpack manager uses Docker to test server compatibility:

```bash
./modpack_manager.sh test --profile [profile_name]
```

This will:
1. Build a Docker image with the specified mods
2. Start a Minecraft server with those mods
3. Analyze the logs for compatibility issues
4. Report any errors or missing dependencies 