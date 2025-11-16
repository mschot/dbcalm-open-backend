# Build environment for DBCalm .rpm packages
# Uses Rocky Linux 9 for compatibility with RHEL 9, AlmaLinux 9, and similar distributions
# Builds binaries with system GLIBC for portability across EL9+ systems

FROM rockylinux:9

ENV TZ=UTC

# Install build dependencies
# Rocky Linux 9 includes Python 3.9 by default, we'll install 3.11
RUN dnf install -y \
    python3.11 \
    python3.11-devel \
    python3.11-pip \
    gcc \
    gcc-c++ \
    make \
    rpm-build \
    rpmdevtools \
    systemd-rpm-macros \
    git \
    && dnf clean all

# Set working directory
WORKDIR /build

# Install Python build tools in a virtual environment
RUN python3.11 -m venv /opt/build-venv \
    && /opt/build-venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/build-venv/bin/pip install pyinstaller

# Add venv to PATH
ENV PATH="/opt/build-venv/bin:$PATH"

# Default command
CMD ["/bin/bash"]
