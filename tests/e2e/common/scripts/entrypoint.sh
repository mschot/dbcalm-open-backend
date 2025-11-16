#!/bin/bash
# Entrypoint script that starts services and runs E2E tests
set -e

echo "=== E2E Test Entrypoint ==="

# Ensure all scripts are executable (needed for volume-mounted scripts)
chmod +x /tests/scripts/*.sh 2>/dev/null || true

# Clean up old logs before starting
echo "Cleaning up old logs..."
rm -f /tests/logs/*.log /tests/logs/dbcalm/*.log 2>/dev/null || true

# Initialize MariaDB if needed (Rocky/RHEL requires explicit initialization)
if [ ! -d "/var/lib/mysql/mysql" ]; then
    echo "Initializing MariaDB data directory..."
    mysql_install_db --user=mysql --datadir=/var/lib/mysql
    echo "MariaDB initialization complete"
fi

# Start MariaDB in the background
echo "Starting MariaDB..."
mysqld_safe --datadir=/var/lib/mysql --log-error=/tests/logs/mariadb-error.log &
MYSQL_PID=$!

# Wait for MariaDB to be ready
echo "Waiting for MariaDB to be ready..."
for i in {1..30}; do
    if mysqladmin ping -h localhost --silent 2>/dev/null; then
        echo "MariaDB is ready!"
        break
    fi
    echo "Waiting for MariaDB... ($i/30)"
    sleep 2
done

if ! mysqladmin ping -h localhost --silent 2>/dev/null; then
    echo "ERROR: MariaDB failed to start"
    exit 1
fi

# Setup MariaDB (create user, database, load schema)
echo "Setting up MariaDB..."
/tests/scripts/setup_mariadb.sh

# Install and setup DBCalm
echo "Setting up DBCalm..."
/tests/scripts/setup_dbcalm.sh

# Source credentials
if [ -f /tmp/e2e_credentials.env ]; then
    source /tmp/e2e_credentials.env
    export E2E_CLIENT_ID E2E_CLIENT_SECRET
    echo "Loaded API client credentials"
else
    echo "ERROR: Credentials file not found at /tmp/e2e_credentials.env"
    exit 1
fi

# Change to test directory
cd /app/tests/e2e/common

# Run tests
echo "=== Running pytest ==="
python3.11 -m pytest -v --tb=short \
    --junitxml=/tests/test-results/junit.xml \
    --log-cli-level=INFO \
    test_backup_restore.py \
    2>&1 | tee /tests/logs/test-output.log

TEST_EXIT_CODE=${PIPESTATUS[0]}

# Cleanup
echo "=== Cleanup ==="
/tests/scripts/cleanup.sh || true

# Stop MariaDB
echo "Stopping MariaDB..."
mysqladmin -u root shutdown 2>/dev/null || kill $MYSQL_PID 2>/dev/null || true

# Make logs readable on host
echo "Making logs readable..."
chmod -R 777 /tests/logs 2>/dev/null || true

echo "=== Tests completed with exit code: $TEST_EXIT_CODE ==="
exit $TEST_EXIT_CODE
