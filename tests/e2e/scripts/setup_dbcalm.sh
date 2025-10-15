#!/bin/bash
set -e

echo "=== Setting up DBCalm for E2E tests ==="

# Find and install the .deb package
DEB_FILE=$(ls /tests/artifacts/*.deb 2>/dev/null | head -1)
if [ -z "$DEB_FILE" ]; then
    echo "ERROR: No .deb package found in /tests/artifacts/"
    exit 1
fi

echo "Installing DBCalm from $DEB_FILE..."
dpkg -i "$DEB_FILE" || apt-get install -f -y

# Create runtime directory (normally done by systemd via RuntimeDirectory)
echo "Creating runtime directory..."
mkdir -p /var/run/dbcalm
chmod 2774 /var/run/dbcalm
chown root:dbcalm /var/run/dbcalm

# Start DBCalm services manually (no systemd in container)
echo "Starting DBCalm services..."
sudo -u root /usr/bin/dbcalm-cmd &
sleep 2
sudo -u mysql /usr/bin/dbcalm-mariadb-cmd &
sleep 2
sudo -u dbcalm /usr/bin/dbcalm server &
sleep 5

# Wait for API server to be ready
echo "Waiting for API server to be ready..."
for i in {1..30}; do
    if curl -k -s https://localhost:8335/docs >/dev/null 2>&1; then
        echo "API server is ready!"
        break
    fi
    echo "Waiting for API server... ($i/30)"
    sleep 2
done

if ! curl -k -s https://localhost:8335/docs >/dev/null 2>&1; then
    echo "ERROR: API server failed to start"
    echo "Checking API server logs..."
    ps aux | grep dbcalm
    exit 1
fi

# Check if dbcalm command is available
if ! command -v dbcalm &> /dev/null; then
    echo "ERROR: dbcalm command not found after installation"
    exit 1
fi

# Create API client for E2E tests
echo "Creating API client for E2E tests..."
output=$(dbcalm clients add "e2e-test-client" 2>&1) || {
    echo "ERROR: dbcalm clients add failed with exit code $?"
    echo "Output: $output"
    exit 1
}

# Extract client_id and client_secret from output
client_id=$(echo "$output" | grep "Client ID:" | awk '{print $3}')
client_secret=$(echo "$output" | grep "Client Secret:" | awk '{print $3}')

if [ -z "$client_id" ] || [ -z "$client_secret" ]; then
    echo "ERROR: Failed to extract client credentials"
    echo "Output was: $output"
    exit 1
fi

# Save credentials to file for pytest
echo "E2E_CLIENT_ID=$client_id" > /tmp/e2e_credentials.env
echo "E2E_CLIENT_SECRET=$client_secret" >> /tmp/e2e_credentials.env

# Also export for current session
export E2E_CLIENT_ID="$client_id"
export E2E_CLIENT_SECRET="$client_secret"

echo "DBCalm setup complete!"
echo "Client ID: $client_id"
echo "Credentials saved to: /tmp/e2e_credentials.env"

# Verify services are running (check processes instead of systemctl)
echo "Verifying DBCalm services..."
ps aux | grep -E "(dbcalm|dbcalm-cmd|dbcalm-mariadb-cmd)" | grep -v grep || echo "Warning: Some services may not be running"

# Verify command sockets
echo ""
/tests/scripts/verify_sockets.sh
