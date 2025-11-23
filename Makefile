SHELL := /bin/bash
VERSION := $(shell grep 'version' pyproject.toml | sed -n 's/version="\([^"]*\)"/\1/p')

.PHONY: hooks dev deb
# Adds git hooks to the project
hooks:
	@if [ -d hooks ]; then \
		for hook in hooks/*; do \
			if [ -f "$$hook" ]; then \
				hook_name=$$(basename $$hook); \
				ln -sf ../../$$hook .git/hooks/$$hook_name; \
				chmod +x .git/hooks/$$hook_name; \
				echo "Installed hook: $$hook_name"; \
			fi \
		done; \
	else \
		echo "No hooks directory found"; \
	fi

# Adds a symlink to the database file so we can
# easily open it in vscode sqlite extension
dbsymlink:
	ln -s /var/lib/dbcalm/db.sqlite3 db.sqlite3

dev-install:
	cd dev && ./install.sh
dev:
	cd dev && source ../.venv/bin/activate && pip install ../ && ./start_all.py

# Clean Python cache files (prevents Docker permission errors)
clean-pycache:
	@echo "Cleaning Python cache files..."
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Build Debian package (local - uses host GLIBC)
deb:
	source .venv/bin/activate && ./build-deb.sh

# Build Debian package in Ubuntu 22.04 Docker container (recommended for production)
# Ensures compatibility with Ubuntu 22.04, 24.04+ (GLIBC 2.35+)
deb-docker: clean-pycache
	@echo "Building .deb in Ubuntu 22.04 container for maximum compatibility..."
	docker build -f build.Dockerfile -t dbcalm-builder:ubuntu22.04 .
	docker run --rm -v $(PWD):/build -w /build dbcalm-builder:ubuntu22.04 bash -c "\
		source /opt/build-venv/bin/activate && \
		pip install -e . && \
		./build-deb.sh"
	@echo "Build complete! Package: dist/dbcalm_$(VERSION)_amd64.deb"

install-deb:
	sudo dpkg -i "dist/dbcalm_${VERSION}_amd64.deb"

reinstall:
	sudo apt remove dbcalm -y && sudo rm -rf /var/log/dbcalm/ && sudo rm -rf /var/lib/dbcalm/ && sudo rm -rf /etc/dbcalm/ && make deb && sudo dpkg -i dist/dbcalm_0.0.1_amd64.deb

# Build RPM package (local - uses host GLIBC)
rpm:
	source .venv/bin/activate && ./build-rpm.sh

# Build RPM package in Rocky Linux 9 Docker container (recommended for production)
# Ensures compatibility with RHEL 9, Rocky 9, AlmaLinux 9+
rpm-docker: clean-pycache
	@echo "Building .rpm in Rocky Linux 9 container for maximum compatibility..."
	docker build -f build-rpm.Dockerfile -t dbcalm-builder:rocky9 .
	docker run --rm -v $(PWD):/build -w /build dbcalm-builder:rocky9 bash -c "\
		source /opt/build-venv/bin/activate && \
		pip install -e . && \
		./build-rpm.sh"
	@echo "Build complete! Package: dist/dbcalm-$(VERSION)-1.el9.x86_64.rpm"

install-rpm:
	sudo dnf install -y "dist/dbcalm-${VERSION}-1.el9.x86_64.rpm"

# End-to-End Tests - MariaDB on Debian/Ubuntu
e2e-test-mariadb-deb: deb-docker
	@echo "Preparing MariaDB Debian E2E test artifacts..."
	@mkdir -p tests/e2e/artifacts
	@cp dist/*.deb tests/e2e/artifacts/
	@echo "Running MariaDB Debian E2E tests in Docker..."
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian DB_TYPE=mariadb docker compose up --build --force-recreate --abort-on-container-exit --exit-code-from test-runner

e2e-test-mariadb-deb-quick:
	@if [ ! -f tests/e2e/artifacts/*.deb ]; then \
		echo "No .deb package found in tests/e2e/artifacts/"; \
		echo "Run 'make e2e-test-mariadb-deb' first to build and test."; \
		exit 1; \
	fi
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian DB_TYPE=mariadb docker compose -p dbcalm-e2e-deb-mariadb up --force-recreate --build --abort-on-container-exit --exit-code-from test-runner

e2e-shell-mariadb-deb:
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian DB_TYPE=mariadb docker compose run --rm test-runner /bin/bash

e2e-clean-mariadb-deb:
	@echo "Cleaning MariaDB Debian E2E test environment..."
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian DB_TYPE=mariadb docker compose down -v || true
	rm -rf tests/e2e/artifacts/*.deb tests/e2e/logs/* tests/e2e/test-results/* || true
	docker system prune -f || true

e2e-logs-mariadb-deb:
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian DB_TYPE=mariadb docker compose -p dbcalm-e2e-deb-mariadb logs --no-color test-runner

# End-to-End Tests - MySQL on Debian/Ubuntu
e2e-test-mysql-deb: deb-docker
	@echo "Preparing MySQL Debian E2E test artifacts..."
	@mkdir -p tests/e2e/artifacts
	@cp dist/*.deb tests/e2e/artifacts/
	@echo "Running MySQL Debian E2E tests in Docker..."
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian DB_TYPE=mysql docker compose up --build --force-recreate --abort-on-container-exit --exit-code-from test-runner

e2e-test-mysql-deb-quick:
	@if [ ! -f tests/e2e/artifacts/*.deb ]; then \
		echo "No .deb package found in tests/e2e/artifacts/"; \
		echo "Run 'make e2e-test-mysql-deb' first to build and test."; \
		exit 1; \
	fi
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian DB_TYPE=mysql docker compose -p dbcalm-e2e-deb-mysql up --force-recreate --build --abort-on-container-exit --exit-code-from test-runner

e2e-shell-mysql-deb:
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian DB_TYPE=mysql docker compose run --rm test-runner /bin/bash

e2e-clean-mysql-deb:
	@echo "Cleaning MySQL Debian E2E test environment..."
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian DB_TYPE=mysql docker compose down -v || true
	rm -rf tests/e2e/artifacts/*.deb tests/e2e/logs/* tests/e2e/test-results/* || true
	docker system prune -f || true

e2e-logs-mysql-deb:
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian DB_TYPE=mysql docker compose -p dbcalm-e2e-deb-mysql logs --no-color test-runner

# End-to-End Tests - MariaDB on Rocky/RHEL
e2e-test-mariadb-rpm: rpm-docker
	@echo "Preparing MariaDB Rocky E2E test artifacts..."
	@mkdir -p tests/e2e/artifacts
	@cp dist/*.rpm tests/e2e/artifacts/
	@echo "Running MariaDB Rocky E2E tests in Docker..."
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky DB_TYPE=mariadb docker compose up --force-recreate --build --abort-on-container-exit --exit-code-from test-runner

e2e-test-mariadb-rpm-quick:
	@if [ ! -f tests/e2e/artifacts/*.rpm ]; then \
		echo "No .rpm package found in tests/e2e/artifacts/"; \
		echo "Run 'make e2e-test-mariadb-rpm' first to build and test."; \
		exit 1; \
	fi
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky DB_TYPE=mariadb docker compose -p dbcalm-e2e-rpm-mariadb up --force-recreate --build --abort-on-container-exit --exit-code-from test-runner

e2e-shell-mariadb-rpm:
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky DB_TYPE=mariadb docker compose run --rm test-runner /bin/bash

e2e-clean-mariadb-rpm:
	@echo "Cleaning MariaDB Rocky E2E test environment..."
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky DB_TYPE=mariadb docker compose down -v || true
	rm -rf tests/e2e/artifacts/*.rpm tests/e2e/logs/* tests/e2e/test-results/* || true
	docker system prune -f || true

e2e-logs-mariadb-rpm:
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky DB_TYPE=mariadb docker compose -p dbcalm-e2e-rpm-mariadb logs --no-color test-runner

# End-to-End Tests - MySQL on Rocky/RHEL
e2e-test-mysql-rpm: rpm-docker
	@echo "Preparing MySQL Rocky E2E test artifacts..."
	@mkdir -p tests/e2e/artifacts
	@cp dist/*.rpm tests/e2e/artifacts/
	@echo "Running MySQL Rocky E2E tests in Docker..."
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky DB_TYPE=mysql docker compose up --force-recreate --build --abort-on-container-exit --exit-code-from test-runner

e2e-test-mysql-rpm-quick:
	@if [ ! -f tests/e2e/artifacts/*.rpm ]; then \
		echo "No .rpm package found in tests/e2e/artifacts/"; \
		echo "Run 'make e2e-test-mysql-rpm' first to build and test."; \
		exit 1; \
	fi
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky DB_TYPE=mysql docker compose -p dbcalm-e2e-rpm-mysql up --force-recreate --build --abort-on-container-exit --exit-code-from test-runner

e2e-shell-mysql-rpm:
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky DB_TYPE=mysql docker compose run --rm test-runner /bin/bash

e2e-clean-mysql-rpm:
	@echo "Cleaning MySQL Rocky E2E test environment..."
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky DB_TYPE=mysql docker compose down -v || true
	rm -rf tests/e2e/artifacts/*.rpm tests/e2e/logs/* tests/e2e/test-results/* || true
	docker system prune -f || true

e2e-logs-mysql-rpm:
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky DB_TYPE=mysql docker compose -p dbcalm-e2e-rpm-mysql logs --no-color test-runner

# Run all E2E tests in parallel (builds packages then runs all test combinations)
e2e-test-all:
	python3 tests/e2e/run_all_tests.py

