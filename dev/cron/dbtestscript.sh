#!/bin/bash

#get parent parent folder of the script
DEV_ROOT="$(dirname "$(dirname "$(readlink -fm "$0")")")"

#load environment variables from .env file
set -a && source ${DEV_ROOT}/.env && set +a

#insert a record into the test table
mysql -u ${MYSQL_USER} -p${MYSQL_PWD} -e "insert into test.test (first_name, last_name, email) values ('John', 'Doe', 'john@doe.com');";
