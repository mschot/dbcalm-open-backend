# E2E Test Environment for DBCalm RPM packages
# Uses Rocky Linux 9 to test RPM installation and functionality

FROM rockylinux:9

ENV TZ=UTC

# Install MariaDB, Python 3.11, and test dependencies
# Use --allowerasing to replace curl-minimal with full curl
RUN dnf install -y --allowerasing \
    mariadb-server \
    mariadb \
    mariadb-backup \
    python3.11 \
    python3.11-pip \
    curl \
    openssl \
    sudo \
    procps \
    && dnf clean all

# Install Python test dependencies
RUN python3.11 -m pip install --upgrade pip \
    && python3.11 -m pip install \
    pytest \
    pytest-timeout \
    requests \
    pymysql \
    cryptography

# Create test directories
RUN mkdir -p /tests/artifacts \
    && mkdir -p /tests/logs \
    && mkdir -p /tests/test-results

# Note: Scripts and fixtures will be mounted as volumes from common/ directory

# Set working directory
WORKDIR /app/tests/e2e/common

# Run entrypoint script
ENTRYPOINT ["/tests/scripts/entrypoint.sh"]
