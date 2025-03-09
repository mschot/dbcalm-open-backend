SHELL := /bin/bash

.PHONY: hooks dev
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
	cd dev && source ../.venv/bin/activate && ./start_both.py

