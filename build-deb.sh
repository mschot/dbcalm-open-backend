#!/bin/bash
set -e


# Get version from pyproject.toml or default to 1.0.0
VERSION=$(grep -oP 'version\s*=\s*"\K[^"]+' pyproject.toml 2>/dev/null || echo "1.0.0")
PACKAGE_NAME="dbcalm"
ARCH="amd64"

#remove old build directory if it exists
rm -rf build/debian

# Create necessary directories
mkdir -p "build/debian/usr/bin"
mkdir -p "build/debian/usr/lib/systemd/system"
mkdir -p "build/debian/DEBIAN"
mkdir -p "build/debian/etc/$PACKAGE_NAME"
mkdir -p "build/debian/var/log/$PACKAGE_NAME"
mkdir -p "build/debian/var/lib/$PACKAGE_NAME"
mkdir -p "build/debian/var/run/$PACKAGE_NAME"
mkdir -p "build/debian/var/backups/$PACKAGE_NAME"

#copy files to the right location
cp "templates/$PACKAGE_NAME-api.service" "build/debian/usr/lib/systemd/system/"
cp "templates/$PACKAGE_NAME-cmd.service" "build/debian/usr/lib/systemd/system/"
cp "templates/$PACKAGE_NAME-mariadb-cmd.service" "build/debian/usr/lib/systemd/system/"
cp templates/DEBIAN/* build/debian/DEBIAN/

echo "Building ${PACKAGE_NAME} version ${VERSION} for ${ARCH}..."

# Create binary executables with pyinstaller
echo "Creating executables..."
pyinstaller --onefile --hidden-import passlib.handlers.bcrypt --clean --workpath=./build/pyinstaller --distpath=dist/production ${PACKAGE_NAME}.py
pyinstaller --onefile --clean --workpath=./build/pyinstaller --distpath=dist/production ${PACKAGE_NAME}-cmd.py
pyinstaller --onefile --clean --workpath=./build/pyinstaller --distpath=dist/production ${PACKAGE_NAME}-mariadb-cmd.py
rm -f ${PACKAGE_NAME}.spec
rm -f ${PACKAGE_NAME}-cmd.spec
rm -f ${PACKAGE_NAME}-mariadb-cmd.spec

# Create necessary directories if they don't exist
mkdir -p "build/debian/usr/bin"

# Copy binaries to the right location
echo "Copying binaries to debian package structure..."
cp "dist/production/${PACKAGE_NAME}" "build/debian/usr/bin/"
cp "dist/production/${PACKAGE_NAME}-cmd" "build/debian/usr/bin/"
cp "dist/production/${PACKAGE_NAME}-mariadb-cmd" "build/debian/usr/bin/"

cp templates/${PACKAGE_NAME}-api.service "build/debian/usr/lib/systemd/system/"
cp templates/${PACKAGE_NAME}-cmd.service "build/debian/usr/lib/systemd/system/"
cp templates/${PACKAGE_NAME}-mariadb-cmd.service "build/debian/usr/lib/systemd/system/"

cp -p templates/config.yml "build/debian/etc/$PACKAGE_NAME/"
cp -p templates/credentials.cnf "build/debian/etc/$PACKAGE_NAME/"

# Update version in control file
sed -i "s/^Version:.*/Version: ${VERSION}/" build/debian/DEBIAN/control

# Build the package
echo "Building Debian package..."
fakeroot dpkg-deb --build build/debian "dist/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

echo "Package created: dist/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"