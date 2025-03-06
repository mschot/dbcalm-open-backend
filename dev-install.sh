#!/bin/bash

# Get the project name from the first argument or use default
project_name=${1:-dbcalm}

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    echo "Please run as root"
    exit 1
fi

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

#create backup dir and set permissions
mkdir -p /var/backups/$project_name/
sudo chown -R mysql:$project_name /var/backups/$project_name/
sudo chmod -R 770 /var/backups/$project_name/

#create run dir and set permissions
mkdir -p /var/run/$project_name/
sudo chown -R mysql:$project_name /var/run/$project_name/
sudo chmod -R 770 /var/run/$project_name/

#create log dir and set permissions
mkdir -p /var/log/$project_name/
sudo chown -R mysql:$project_name /var/log/$project_name/
sudo chmod -R 770 /var/log/$project_name/

#copy config file to /etc/$project_name/
mkdir -p /etc/$project_name/
cp templates/config.yml /etc/$project_name/

if [ -f "/etc/systemd/system/$project_name-cmd.service" ]; then
    systemctl stop "$project_name-cmd"
fi
#create executable and copy to /usr/bin
pyinstaller --onefile --clean $project_name-cmd-server.py
cp dist/$project_name-cmd-server /usr/bin/
chown mysql:$project_name /usr/bin/$project_name-cmd-server
chmod 750 /usr/bin/$project_name-cmd-server

#copy service file to /etc/systemd/system/
cp templates/$project_name-cmd.service /usr/lib/systemd/system/
systemctl daemon-reload
systemctl restart $project_name-cmd

#create lib dirs and set permissions
mkdir -p "/var/lib/$project_name"
chgrp "$project_name" "/var/lib/$project_name"
chmod 775 "/var/lib/$project_name"
