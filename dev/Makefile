ifneq (,$(wildcard ./.env))
    include .env
    export
endif

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

#REQUIRES sudo, to add cron e.g. sudo make addcron
addcron:
	echo  "* * * * *    root    $(ROOT_DIR)/cron/dbtestscript.sh" > /etc/cron.d/backrest-dbtest

#REQUIRES sudo to remove cron, e.g. sudo make removecron
removecron:
	rm /etc/cron.d/backrest-dbtest

.SILENT:
checkdb:
	mysql -u ${MYSQL_USER} -p${MYSQL_PWD} -e "SELECT * FROM test.test ORDER BY created_at DESC LIMIT 10";
	
	