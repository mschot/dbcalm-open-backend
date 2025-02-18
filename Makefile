SHELL := /bin/bash

.PHONY: hooks

# Adds git hooks to the project
hooks:
	ln -s -f ../hooks .git/hooks

# Adds a symlink to the database file so we can open
# it in vscode sqlite extension
dbsymlink:
	ln -s /var/lib/backrest/db.sqlite3 db.sqlite3


