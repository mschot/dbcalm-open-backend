# Getting Started

## Set up groups and folders
```
sudo make dev-install
```

## SSL Certificate
To ensure security when entering your credentials you will need a certificate. One of the easiest ways to get one for local developemnt is to use mkcert, or for public urls use let's encrypt. 

Then store them in 

```
/etc/dbcalm/ssl/fullchain-cert.pem
/etc/dbcalm/ssl/private-key.pem
```

Then set the permissions:

```
sudo chown dbcalm:dbcalm /etc/dbcalm/ssl/*
```

## Run the API - and required command server
As there are 2 parts that need watching, a cmd server and the api to run these both with a change watcher run:

```
make dev
```

It will complain about sudo requiring -s, this is because the command server wants to run as as the mysql user so mariabackup has permissions to access to the mysql files that it wants to backup .

To get around this, in ubuntu add a new file /etc/sudoers.d/dbcalm with 

```
your-username ALL=(mysql) NOPASSWD: /your/path/to/.venv/bin/python3 dbcalm-cmd-server.py
# Allow creating and managing the runtime directory
your-username ALL=(root) NOPASSWD: /usr/bin/mkdir -p /var/run/dbcalm
your-username ALL=(root) NOPASSWD: /usr/bin/chown dbcalm\:dbcalm /var/run/dbcalm
your-username ALL=(root) NOPASSWD: /usr/bin/chmod 2774 /var/run/dbcalm

# Allow running dbcalm.py as dbcalm user
your-username ALL=(dbcalm) NOPASSWD: /your/path/to/.venv/bin/python3 dbcalm.py server
```
you might have to log out or restart for this to take effect

## Add Users
Once everything (including frontend) is up and running you will need a user to log in.
To add new users run `./dbcalm.py users` or `make users` from the root folder.