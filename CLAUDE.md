# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Test server: `python modpack_manager/scripts/commands/test_server.py --profile <profile_name>`
- Create server: `python modpack_manager/scripts/commands/create_server_pack.py --profile <profile_name>`
- List mods: `python modpack_manager/scripts/commands/list_mods.py --profile <profile_name>`
- Add mod: `python modpack_manager/scripts/commands/add_mod.py --profile <profile_name> --mod-id <mod_id>`

## Code Style
- Python: Maintain compatibility with both Python 2.7 and 3+
- Imports: Group as `standard_library`, `third_party`, `local_application`
- Functions/variables: Use `snake_case`
- Classes: Use `PascalCase`
- Constants: Use `UPPER_CASE`
- Docstrings: Google-style with parameters and return values documented
- Error handling: Use specific exceptions with descriptive messages
- Log meaningful events, use appropriate log levels

## Project Structure
- `modpack_manager/`: Core functionality for managing Minecraft modpacks
- `modpack_manager/scripts/commands/`: Command-line scripts for modpack operations
- `DOCS/`: Documentation for users and developers
- `AISPEC/`: API specifications and integration guidelines