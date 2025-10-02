# Dbcalm Project Guide

## Build & Run Commands
- Run server: `python main.py` or `cd dev && make dev`
- Lint: `ruff check .` or `ruff check . --fix`
- Tests: `.venv/bin/python -m pytest tests/`
- Pre-commit hook (runs automatically): Runs linter and tests
- Build command binary: `pyinstaller dbcalm-cmd-server.py`

### Development Setup Requirements
The development environment (`make dev`) runs the cmd_server_process as the mysql user for security. Configure passwordless sudo by adding to `/etc/sudoers.d/dbcalm`:
```
your_user ALL=(mysql) NOPASSWD: /usr/bin/python3 /full/path/to/dbcalm-cmd-server.py
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
- `/dbcalm_client`: Client library for interacting with the command Service tool via unix domain socket
- `/dbcalm-cmd-server.py`: Service tool entry point executing backups and restores
- `/dbcalm_cmd_server`: Command Service for interacting with mariabackup and mysqladmin