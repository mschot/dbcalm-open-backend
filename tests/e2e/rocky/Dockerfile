# E2E Test Environment for DBCalm RPM packages
# Uses Rocky Linux 9 to test RPM installation and functionality

FROM rockylinux:9

# Build argument to select database type (mariadb or mysql)
ARG DB_TYPE=mariadb

ENV TZ=UTC

# Install base dependencies and Python
# Use --allowerasing to replace curl-minimal with full curl
RUN dnf install -y --allowerasing \
    python3.11 \
    python3.11-pip \
    curl \
    openssl \
    sudo \
    procps \
    file \
    && dnf clean all

# Install Percona repository and XtraBackup
RUN dnf install -y https://repo.percona.com/yum/percona-release-latest.noarch.rpm \
    && percona-release enable-only tools release \
    && dnf install -y percona-xtrabackup-80 \
    && dnf clean all

# Install database server based on DB_TYPE build arg
RUN if [ "$DB_TYPE" = "mariadb" ]; then \
        dnf install -y mariadb-server mariadb mariadb-backup; \
    else \
        dnf install -y mysql-server mysql; \
    fi \
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
