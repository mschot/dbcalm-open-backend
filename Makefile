SHELL := /bin/bash

.PHONY: hooks

# Adds git hooks to the project
hooks:
	ln -s -f ../hooks .git/hooks

# Adds a symlink to the database file so we can open
# it in vscode sqlite extension
dbsymlink:
	ln -s /var/lib/backrest/db.sqlite3 db.sqlite3

socket:
	mkdir /var/run/backrest
	chown backrest:backrest /var/run/backrest
	chmod 770 /var/run/backrest

kill:
	@for pid in $$(ps aux | grep "python -B -c" | grep -v grep | awk '{print $$2}'); do \
		kill -9 $$pid; \
	done