# Dbcalm Project Guide

## Build & Run Commands
- Run API server: `python dbcalm.py server` or `cd dev && make dev`
- Manage users: `python dbcalm.py users [add|delete|update-password|list]`
- Manage clients: `python dbcalm.py clients [add|delete|update|list]`
- Lint: `ruff check .` or `ruff check . --fix`
- Tests: `.venv/bin/python -m pytest tests/`
- Pre-commit hook (runs automatically): Runs linter and tests
- Build binaries: `pyinstaller dbcalm.py` and `pyinstaller dbcalm-mariadb-cmd.py`

### Development Setup Requirements
The development environment (`make dev`) runs the mariadb_cmd_process as the mysql user for security. Configure passwordless sudo by adding to `/etc/sudoers.d/dbcalm`:
```
your_user ALL=(mysql) NOPASSWD: /usr/bin/python3 /full/path/to/dbcalm-mariadb-cmd.py
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
- `/dbcalm_mariadb_cmd_client`: Client library for interacting with the MariaDB command service via unix domain socket
- `/dbcalm.py`: Main CLI entry point (API server, user/client management)
- `/dbcalm-mariadb-cmd.py`: MariaDB command service entry point executing backups and restores
- `/dbcalm_mariadb_cmd`: MariaDB command service for interacting with mariabackup and mysqladmin