#!/bin/bash

# Get the project name from the first argument or use default
project_name=${1:-dbcalm}

if [ "$EUID" -ne 0 ]; then
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

if [ -n "$SUDO_USER" ] && ! id -nG "$SUDO_USER" | grep -qw "$project_name"; then
    usermod -a -G $project_name "$SUDO_USER"
fi

if ! id "$project_name" >/dev/null 2>&1; then
    #no login and no home
    useradd -r -s /usr/sbin/nologin -M -g $project_name $project_name
fi

#change working directory to parent directory
cd "$(dirname "$0")/../"

# activate .venv
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

#copy config file to /etc/$project_name/ and create ssl directory
mkdir -p /etc/$project_name/ssl/
cp templates/config.yml /etc/$project_name/

#create lib dirs and set permissions
mkdir -p "/var/lib/$project_name"
chgrp "$project_name" "/var/lib/$project_name"
chmod 775 "/var/lib/$project_name"
