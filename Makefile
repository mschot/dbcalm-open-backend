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

# Build Debian package
deb:
	source .venv/bin/activate && ./build-deb.sh

install-deb:
	sudo dpkg -i "dist/dbcalm_${VERSION}_amd64.deb"

users:
	source .venv/bin/activate && ./dbcalm.py users

clients:
	source .venv/bin/activate && ./dbcalm.py clients

reinstall:
	sudo apt remove dbcalm -y && sudo rm -rf /var/log/dbcalm/ && sudo rm -rf /var/lib/dbcalm/ && sudo rm -rf /etc/dbcalm/ && make deb && sudo dpkg -i dist/dbcalm_0.0.1_amd64.deb

