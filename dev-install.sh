#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"    
    exit 1

fi

project_name="backrest"

if ! getent group $project_name >/dev/null 2>&1; then
    groupadd $project_name
fi

if ! id -nG mysql | grep -qw "$project_name"; then
    usermod -a -G $project_name mysql
fi

if ! id "$project_name" >/dev/null 2>&1; then
    #no login and no home
    useradd -r -s /usr/sbin/nologin -M -g $project_name $project_name
fi

cd "$(dirname "$0")"
source .venv/bin/activate

pyinstaller --onefile --clean mariadb-cmd.py
cp dist/mariadb-cmd /usr/bin/
chown mysql:$project_name /usr/bin/mariadb-cmd
chmod 750 /usr/bin/mariadb-cmd

cp templates/$project_name-mariadb-cmd.service /etc/systemd/system/
systemctl daemon-reload
systemctl restart $project_name-mariadb-cmd





