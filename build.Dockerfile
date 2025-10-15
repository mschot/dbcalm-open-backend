# Build environment for DBCalm .deb packages
# Uses Ubuntu 22.04 (GLIBC 2.35) for compatibility with Ubuntu 22.04, 24.04+
# Builds binaries with older GLIBC than host (2.39) to ensure portability

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install build dependencies
# Ubuntu 22.04 includes Python 3.10 by default, install 3.11 from universe
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    build-essential \
    dpkg-dev \
    fakeroot \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Install Python build tools in a virtual environment
RUN python3.11 -m venv /opt/build-venv \
    && /opt/build-venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/build-venv/bin/pip install pyinstaller

# Default command
CMD ["/bin/bash"]
