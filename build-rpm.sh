#!/bin/bash
set -e

# Get version from environment variable, or from pyproject.toml, or default to 1.0.0
if [ -z "$VERSION" ]; then
  VERSION=$(grep -oP 'version\s*=\s*"\K[^"]+' pyproject.toml 2>/dev/null || echo "1.0.0")
fi
PACKAGE_NAME="dbcalm"
ARCH="x86_64"

# Remove old build directory if it exists
rm -rf build/rpm

# Create RPM build directory structure
mkdir -p "build/rpm/BUILD"
mkdir -p "build/rpm/RPMS"
mkdir -p "build/rpm/SOURCES"
mkdir -p "build/rpm/SPECS"
mkdir -p "build/rpm/SRPMS"

# Create staging directory for pre-built files (will be copied by spec file)
mkdir -p "build/rpm/staging/usr/bin"
mkdir -p "build/rpm/staging/usr/lib/systemd/system"
mkdir -p "build/rpm/staging/etc/$PACKAGE_NAME"
mkdir -p "build/rpm/staging/var/log/$PACKAGE_NAME"
mkdir -p "build/rpm/staging/var/lib/$PACKAGE_NAME"
mkdir -p "build/rpm/staging/var/run/$PACKAGE_NAME"
mkdir -p "build/rpm/staging/var/backups/$PACKAGE_NAME"
mkdir -p "build/rpm/staging/usr/share/$PACKAGE_NAME/scripts"

# Pre-create empty database file to be included in package
touch "build/rpm/staging/var/lib/$PACKAGE_NAME/db.sqlite3"

echo "Building ${PACKAGE_NAME} version ${VERSION} for ${ARCH}..."

# Create binary executables with pyinstaller
echo "Creating executables..."
pyinstaller --onefile --hidden-import passlib.handlers.bcrypt --clean --workpath=./build/pyinstaller --distpath=dist/production ${PACKAGE_NAME}.py
pyinstaller --onefile --clean --workpath=./build/pyinstaller --distpath=dist/production ${PACKAGE_NAME}-cmd.py
pyinstaller --onefile --clean --workpath=./build/pyinstaller --distpath=dist/production ${PACKAGE_NAME}-mariadb-cmd.py
rm -f ${PACKAGE_NAME}.spec
rm -f ${PACKAGE_NAME}-cmd.spec
rm -f ${PACKAGE_NAME}-mariadb-cmd.spec

# Copy binaries to staging directory
echo "Copying binaries to staging directory..."
cp "dist/production/${PACKAGE_NAME}" "build/rpm/staging/usr/bin/"
cp "dist/production/${PACKAGE_NAME}-cmd" "build/rpm/staging/usr/bin/"
cp "dist/production/${PACKAGE_NAME}-mariadb-cmd" "build/rpm/staging/usr/bin/"

# Copy systemd service files to staging
cp "templates/${PACKAGE_NAME}-api.service" "build/rpm/staging/usr/lib/systemd/system/"
cp "templates/${PACKAGE_NAME}-cmd.service" "build/rpm/staging/usr/lib/systemd/system/"
cp "templates/${PACKAGE_NAME}-mariadb-cmd.service" "build/rpm/staging/usr/lib/systemd/system/"

# Copy configuration files to staging
cp -p "templates/config.yml" "build/rpm/staging/etc/$PACKAGE_NAME/"
cp -p "templates/credentials.cnf" "build/rpm/staging/etc/$PACKAGE_NAME/"

# Copy shared scripts to staging
cp templates/scripts/*.sh "build/rpm/staging/usr/share/$PACKAGE_NAME/scripts/"
chmod +x "build/rpm/staging/usr/share/$PACKAGE_NAME/scripts/"*.sh

# Copy and update spec file
cp "templates/SPEC/${PACKAGE_NAME}.spec" "build/rpm/SPECS/"
sed -i "s/^Version:.*/Version:        ${VERSION}/" "build/rpm/SPECS/${PACKAGE_NAME}.spec"

# Build the RPM package
echo "Building RPM package..."
rpmbuild --define "_topdir $(pwd)/build/rpm" \
         --define "_buildroot $(pwd)/build/rpm/BUILDROOT" \
         --define "version ${VERSION}" \
         -bb "build/rpm/SPECS/${PACKAGE_NAME}.spec"

# Move the built RPM to dist directory
mkdir -p dist
mv "build/rpm/RPMS/${ARCH}/${PACKAGE_NAME}-${VERSION}"*.rpm "dist/"

echo "Package created: dist/${PACKAGE_NAME}-${VERSION}-1.el9.${ARCH}.rpm"

# Clean up temporary build artifacts
echo "Cleaning up build artifacts..."
rm -rf dist/production
