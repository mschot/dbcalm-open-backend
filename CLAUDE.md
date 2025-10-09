# Dbcalm Project Guide

## Build & Run Commands
- Run API server: `python dbcalm.py server` or `cd dev && make dev`
- Manage users: `python dbcalm.py users [add|delete|update-password|list]`
- Manage clients: `python dbcalm.py clients [add|delete|update|list]`
- Lint: `ruff check .` or `ruff check . --fix`
- Tests: `.venv/bin/python -m pytest tests/`
- Pre-commit hook (runs automatically): Runs linter and tests
- Build binaries: `pyinstaller dbcalm.py`, `pyinstaller dbcalm-mariadb-cmd.py`, and `pyinstaller dbcalm-cmd.py`

### Development Setup Requirements
The development environment (`make dev`) runs two command services with different privileges:
- `mariadb_cmd_process`: Runs as mysql user for backup/restore operations
- `cmd_process`: Runs as root for system operations (service management, ownership fixes)

Configure passwordless sudo by adding to `/etc/sudoers.d/dbcalm`:
```
your_user ALL=(mysql) NOPASSWD: /usr/bin/python3 /full/path/to/dbcalm-mariadb-cmd.py
your_user ALL=(root) NOPASSWD: /usr/bin/python3 /full/path/to/dbcalm-cmd.py
```
Replace `your_user` with your username and `/full/path/to` with the absolute path to the backend directory.

## Code Style Guidelines
- Python 3.11+ required
- Use FastAPI framework conventions
- Linting: Ruff (`tool.ruff.lint` in pyproject.toml)
- Structure: Follow domain-driven design with modular components
- Imports: Group standard lib first, then third-party, then local
- Naming: snake_case for functions/variables, PascalCase for classes
- Error handling: Use appropriate exceptions with descriptive messages
- Type hints: Use throughout codebase
- Architecture pattern: Repository pattern with adapters
- Comments: Docstrings for public interfaces, TODOs with noqa: FIX002
- Use Path from pathlib instead of os operations where possible
- Use f-strings for string formatting
- Use double quotes for strings
- Use comma after last item in list/tuple/dict/set if multiline


## Project Organization
- `/dbcalm`: Core server code
- `/dbcalm/cli`: CLI commands (server, users, clients)
- `/dbcalm.py`: Main CLI entry point (API server, user/client management)

### Command Services
The project uses two separate command services for privilege separation:

#### Generic Command Service (root privileges)
- `/dbcalm-cmd.py`: Entry point for system operations requiring root
- `/dbcalm_cmd`: Generic command service package
  - `/process`: Shared process runner (used by both services)
  - `/adapter`: System command adapters (systemctl, chown)
  - `/command`: Whitelist-based validator
- `/dbcalm_cmd_client`: Client library for interacting with generic cmd service via unix domain socket
- **Socket**: `/var/run/dbcalm/cmd.sock`
- **Purpose**: Execute whitelisted system operations (restart services, fix ownership)
- **Security**: Whitelist-based validation, no arbitrary command execution

#### MariaDB Command Service (mysql user privileges)
- `/dbcalm-mariadb-cmd.py`: Entry point for MariaDB backup/restore operations
- `/dbcalm_mariadb_cmd`: MariaDB-specific command service package
  - `/adapter`: MariaDB backup/restore adapters
  - `/builder`: mariabackup command builders
  - `/command`: Backup/restore validator
- `/dbcalm_mariadb_cmd_client`: Client library for interacting with MariaDB cmd service
- **Socket**: `/var/run/dbcalm/mariadb-cmd.sock`
- **Purpose**: Execute mariabackup and mysqladmin commands
- **Security**: Runs as mysql user, validates backup operations