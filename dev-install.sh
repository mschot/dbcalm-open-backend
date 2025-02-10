#!/bin/bash

# Get the project name from the first argument or use default
project_name=${1:-backrest}

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    echo "Please run as root"    
    exit 1
fi

project_name="backrest"

# create group and user if not exists
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

# activate .venv
cd "$(dirname "$0")"
source .venv/bin/activate

if [ -f "/etc/systemd/system/$project_name-mariadb-cmd.service" ]; then
    systemctl stop "$project_name-mariadb-cmd"
fi
#create executable and copy to /usr/bin
pyinstaller --onefile --clean mariadb-cmd.py
cp dist/mariadb-cmd /usr/bin/
chown mysql:$project_name /usr/bin/mariadb-cmd
chmod 750 /usr/bin/mariadb-cmd

#copy service file to /etc/systemd/system/
cp templates/$project_name-mariadb-cmd.service /etc/systemd/system/
systemctl daemon-reload
systemctl restart $project_name-mariadb-cmd

#create lib dirs and set permissions
mkdir -p "/var/lib/$project_name"
chgrp "$project_name" "/var/lib/$project_name"
chmod 775 "/var/lib/$project_name"
