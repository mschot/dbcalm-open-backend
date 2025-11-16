# End-to-End Tests for DBCalm

Comprehensive E2E tests that validate the complete backup and restore workflow using a real MariaDB database in a Docker container with systemd.

## Test Coverage

### 1. Full Backup and Restore
- Creating full backups via API
- Restoring from full backups
- Verifying data integrity after restore

### 2. Incremental Backup and Restore
- Creating incremental backups based on full backups
- Restoring incremental backup chain (full + incremental)
- Validating all data after incremental restore

### 3. Credentials Validation
- Backup fails when credentials file is missing
- Backup fails when `[client-dbcalm]` section is missing

### 4. Restore Preconditions
- Restore fails when MariaDB is running
- Restore fails when data directory is not empty

### 5. Backup Management
- Listing backups via API
- Retrieving backup details

## Running Tests

### Locally (Recommended for Development)

```bash
# Build .deb and run all E2E tests
make e2e-test

# Run tests with existing .deb (faster for iterations)
make e2e-test-quick

# Open shell in test container for debugging
make e2e-shell

# View test logs
make e2e-logs

# Clean up E2E environment
make e2e-clean
```

### Directly with Docker Compose

```bash
# Build and run
cd tests/e2e
docker compose up --build --abort-on-container-exit

# Clean up
docker compose down -v
```

### In GitHub Actions

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual workflow dispatch

## Test Architecture

```
tests/e2e/
├── Dockerfile                   # Ubuntu 22.04 + systemd + MariaDB
├── docker-compose.yml           # Container orchestration
├── fixtures/
│   ├── test_schema.sql         # Test database schema (users, orders)
│   ├── initial_data.sql        # Initial dataset (5 users, 5 orders)
│   └── incremental_data.sql    # Incremental dataset (3 users, 2 orders)
├── scripts/
│   ├── setup_mariadb.sh        # Initialize MariaDB, create backup user
│   ├── setup_dbcalm.sh         # Install .deb, create API client
│   └── cleanup.sh              # Reset state between tests
├── conftest.py                  # Pytest fixtures
├── utils.py                     # Helper functions
└── test_backup_restore.py       # E2E test cases
```

## Test Flow

1. **Container Setup**: Ubuntu + systemd + MariaDB
2. **MariaDB Init**: Create `backupuser`, load test schema
3. **DBCalm Install**: Install .deb package, start services
4. **API Client**: Create client credentials, get bearer token
5. **Run Tests**: Execute pytest test suite
6. **Cleanup**: Stop services, remove containers

## Authentication

Tests use **API clients** (not users) for backend operations:
- API client created automatically during setup
- Client credentials stored in `/tmp/e2e_credentials.env`
- Bearer token obtained via client credentials OAuth flow

## Debugging

### View logs in running container
```bash
docker compose exec test-runner journalctl -u dbcalm-api -f
docker compose exec test-runner journalctl -u dbcalm-mariadb-cmd -f
```

### Interactive debugging
```bash
make e2e-shell

# Inside container:
systemctl status mariadb
systemctl status dbcalm-api
mysql -u root testdb
pytest -v --pdb test_backup_restore.py
```

### Check test output
```bash
cat tests/e2e/logs/test-output.log
cat tests/e2e/test-results/junit.xml
```

## Test Data

### Initial Dataset (after full backup)
- **users**: alice, bob, charlie, diana, eve (5 rows)
- **orders**: ORD-001 through ORD-005 (5 rows)

### Incremental Dataset (after incremental backup)
- **Additional users**: frank, grace, henry (3 rows)
- **Additional orders**: ORD-006, ORD-007 (2 rows)
- **Updates**: charlie's email updated, order #4 status changed

## Requirements

- Docker and Docker Compose
- Python 3.11+
- Make (for convenience commands)
- At least 2GB free disk space
- At least 4GB RAM

## Troubleshooting

### Tests fail with "MariaDB not ready"
- Increase wait time in `setup_mariadb.sh`
- Check MariaDB logs: `docker compose logs test-runner`

### Tests fail with "API client creation failed"
- Verify .deb installation: `docker compose exec test-runner dpkg -l | grep dbcalm`
- Check service status: `docker compose exec test-runner systemctl status dbcalm-api`

### Tests fail with credentials error
- Ensure credentials file exists: `docker compose exec test-runner cat /etc/dbcalm/credentials.cnf`
- Verify [client-dbcalm] section is present

### Container won't start
- Try rebuilding: `docker compose build --no-cache`
- Check Docker daemon: `docker info`
- Ensure systemd is supported: `docker run --privileged ubuntu:22.04 /lib/systemd/systemd`

## CI/CD Integration

GitHub Actions workflow (`.github/workflows/e2e-tests.yml`):
- Builds .deb package from source
- Runs all E2E tests in Docker
- Uploads test results and logs as artifacts
- Reports test summary in PR comments

## Performance

- **Build time**: ~3-5 minutes (container + .deb)
- **Test execution**: ~3-5 minutes (all test scenarios)
- **Total CI/CD time**: ~8-12 minutes

## Future Enhancements

- [ ] Test scheduled backups (cron)
- [ ] Test backup retention policies
- [ ] Test restore to different target (not just database)
- [ ] Test multiple incremental backup chains
- [ ] Test backup verification/validation
- [ ] Test failure recovery scenarios
- [ ] Add performance benchmarks
