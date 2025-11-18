FROM ubuntu:22.04

# Build argument to select database type (mariadb or mysql)
ARG DB_TYPE=mariadb

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install base dependencies and Python
RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    lsb-release \
    gnupg \
    curl \
    ca-certificates \
    python3.11 \
    python3-pip \
    python3.11-venv \
    sudo \
    procps \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Percona repository and XtraBackup
RUN wget https://repo.percona.com/apt/percona-release_latest.$(lsb_release -sc)_all.deb \
    && dpkg -i percona-release_latest.$(lsb_release -sc)_all.deb \
    && percona-release enable-only tools release \
    && apt-get update \
    && apt-get install -y percona-xtrabackup-80 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* percona-release_latest.*.deb

# Install database server based on DB_TYPE build arg
RUN apt-get update && \
    if [ "$DB_TYPE" = "mariadb" ]; then \
        apt-get install -y mariadb-server mariadb-client mariadb-backup; \
    else \
        apt-get install -y mysql-server mysql-client; \
    fi \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create test directories with proper permissions
RUN mkdir -p /tests/fixtures \
    /tests/scripts \
    /tests/artifacts \
    /tests/logs \
    /tests/logs/dbcalm \
    /tests/test-results && \
    chmod -R 777 /tests/logs /tests/test-results /tests/artifacts

# Note: Scripts and fixtures will be mounted as volumes from common/ directory

# Install Python test dependencies
RUN python3.11 -m pip install --no-cache-dir \
    pytest>=8.0.0 \
    requests>=2.31.0 \
    pymysql>=1.1.0 \
    cryptography>=41.0.0

# Configure MariaDB for testing
RUN mkdir -p /var/run/mysqld && \
    chown mysql:mysql /var/run/mysqld

# Create DBCalm directories with proper permissions
RUN mkdir -p /var/backups/dbcalm \
    /var/lib/dbcalm \
    /var/log/dbcalm \
    /var/run/dbcalm \
    /etc/dbcalm/ssl && \
    chmod 755 /var/backups/dbcalm \
    /var/lib/dbcalm \
    /var/log/dbcalm \
    /var/run/dbcalm

# Expose ports
EXPOSE 8335 3306

# Set working directory
WORKDIR /app/tests/e2e/common

# Run entrypoint script (mounted as volume from common/)
ENTRYPOINT ["/tests/scripts/entrypoint.sh"]
