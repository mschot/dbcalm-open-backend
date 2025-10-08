SHELL := /bin/bash
VERSION := $(shell grep 'version' pyproject.toml | sed -n 's/version="\([^"]*\)"/\1/p')

.PHONY: hooks dev deb
# Adds git hooks to the project
hooks:
	ln -s -f ../hooks .git/hooks

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
	./build-deb.sh

install-deb:
	sudo dpkg -i "dist/dbcalm_${VERSION}_amd64.deb"

users:
	source .venv/bin/activate && ./dbcalm.py users

clients:
	source .venv/bin/activate && ./dbcalm.py clients

