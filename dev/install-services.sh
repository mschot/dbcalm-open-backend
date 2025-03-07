#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

#run install.sh
./install.sh

#change working directory to parent directory
cd "$(dirname "$0")/.."

# activate .venv
source .venv/bin/activate

project_name="dbcalm"

#creat servives variable to hold 2 services
services=("$project_name-cmd-server" "$project_name-api")

#loop through services and create them
for service in "${services[@]}"
do
    if [ -f "/usr/lib/systemd/system/$service.service" ]; then
        systemctl stop $service
    fi
    #create executable and copy to /usr/bin
    pyinstaller --onefile --clean $service.py
    cp dist/$service  /usr/bin/
    chown mysql:$project_name /usr/bin/$service
    chmod 750 /usr/bin/$service

    #copy service file to /etc/systemd/system/
    cp templates/$service.service /usr/lib/systemd/system/
    systemctl daemon-reload
    systemctl enable $service
    systemctl restart $service
done