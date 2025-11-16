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

# Build Debian package (local - uses host GLIBC)
deb:
	source .venv/bin/activate && ./build-deb.sh

# Build Debian package in Ubuntu 22.04 Docker container (recommended for production)
# Ensures compatibility with Ubuntu 22.04, 24.04+ (GLIBC 2.35+)
deb-docker:
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
rpm-docker:
	@echo "Building .rpm in Rocky Linux 9 container for maximum compatibility..."
	docker build -f build-rpm.Dockerfile -t dbcalm-builder:rocky9 .
	docker run --rm -v $(PWD):/build -w /build dbcalm-builder:rocky9 bash -c "\
		source /opt/build-venv/bin/activate && \
		pip install -e . && \
		./build-rpm.sh"
	@echo "Build complete! Package: dist/dbcalm-$(VERSION)-1.el9.x86_64.rpm"

install-rpm:
	sudo dnf install -y "dist/dbcalm-${VERSION}-1.el9.x86_64.rpm"

# End-to-End Tests - Debian/Ubuntu
# Build .deb in Ubuntu 22.04 container and run E2E tests
e2e-test: deb-docker
	@echo "Preparing Debian E2E test artifacts..."
	@mkdir -p tests/e2e/artifacts
	@cp dist/*.deb tests/e2e/artifacts/
	@echo "Running Debian E2E tests in Docker..."
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian docker compose up --build --force-recreate --abort-on-container-exit --exit-code-from test-runner

# Run E2E tests with existing .deb (faster for iterative testing)
e2e-test-quick:
	@if [ ! -f tests/e2e/artifacts/*.deb ]; then \
		echo "No .deb package found in tests/e2e/artifacts/"; \
		echo "Run 'make e2e-test' first to build and test."; \
		exit 1; \
	fi
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian docker compose up --abort-on-container-exit --exit-code-from test-runner

# Open shell in Debian test container for debugging
e2e-shell:
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian docker compose run --rm test-runner /bin/bash

# Clean up Debian E2E test environment
e2e-clean:
	@echo "Cleaning Debian E2E test environment..."
	cd tests/e2e/common && DISTRO=debian DISTRO_DIR=debian docker compose down -v || true
	rm -rf tests/e2e/artifacts/*.deb tests/e2e/logs/* tests/e2e/test-results/* || true
	docker system prune -f || true

# View Debian E2E test logs
e2e-logs:
	@if [ -f tests/e2e/logs/test-output.log ]; then \
		cat tests/e2e/logs/test-output.log; \
	else \
		echo "No test logs found. Run 'make e2e-test' first."; \
	fi

# End-to-End Tests - Rocky/RHEL
# Build .rpm in Rocky Linux 9 container and run E2E tests
e2e-test-rpm: rpm-docker
	@echo "Preparing Rocky E2E test artifacts..."
	@mkdir -p tests/e2e/artifacts
	@cp dist/*.rpm tests/e2e/artifacts/
	@echo "Running Rocky E2E tests in Docker..."
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky docker compose up --force-recreate --build --abort-on-container-exit --exit-code-from test-runner

# Run RPM E2E tests with existing .rpm (faster for iterative testing)
e2e-test-rpm-quick:
	@if [ ! -f tests/e2e/artifacts/*.rpm ]; then \
		echo "No .rpm package found in tests/e2e/artifacts/"; \
		echo "Run 'make e2e-test-rpm' first to build and test."; \
		exit 1; \
	fi
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky docker compose up --abort-on-container-exit --exit-code-from test-runner

# Open shell in Rocky test container for debugging
e2e-shell-rpm:
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky docker compose run --rm test-runner /bin/bash

# Clean up Rocky E2E test environment
e2e-clean-rpm:
	@echo "Cleaning Rocky E2E test environment..."
	cd tests/e2e/common && DISTRO=rocky DISTRO_DIR=rocky docker compose down -v || true
	rm -rf tests/e2e/artifacts/*.rpm tests/e2e/logs/* tests/e2e/test-results/* || true
	docker system prune -f || true

# View Rocky E2E test logs
e2e-logs-rpm:
	@if [ -f tests/e2e/logs/test-output.log ]; then \
		cat tests/e2e/logs/test-output.log; \
	else \
		echo "No test logs found. Run 'make e2e-test-rpm' first."; \
	fi

