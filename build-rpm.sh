#!/bin/bash
set -e

# RPM Build Script for DBCalm
# This is a placeholder for future RPM package support
# Will be implemented when RPM distribution is needed

echo "=========================================="
echo "DBCalm RPM Build Script"
echo "=========================================="
echo ""
echo "RPM build support is planned for future implementation."
echo ""
echo "When implemented, this script will:"
echo "  - Build RPM packages for RHEL/Rocky/AlmaLinux"
echo "  - Use rpmbuild with templates/SPEC/dbcalm.spec"
echo "  - Create packages compatible with RHEL 8+/Rocky 9+"
echo "  - Package format: dbcalm-VERSION.x86_64.rpm"
echo ""
echo "Current focus: Debian/Ubuntu (.deb) packages"
echo "=========================================="

# Get version from pyproject.toml for future use
VERSION=$(grep -oP 'version\s*=\s*"\K[^"]+' pyproject.toml 2>/dev/null || echo "1.0.0")
PACKAGE_NAME="dbcalm"

echo ""
echo "Detected version: ${VERSION}"
echo "Target package: ${PACKAGE_NAME}-${VERSION}.x86_64.rpm"
echo ""

exit 0
