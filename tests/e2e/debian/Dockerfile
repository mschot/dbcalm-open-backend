FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install MariaDB, Python, and other dependencies (no systemd needed)
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    mariadb-server \
    mariadb-client \
    mariadb-backup \
    python3.11 \
    python3-pip \
    python3.11-venv \
    sudo \
    curl \
    ca-certificates \
    procps \
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
