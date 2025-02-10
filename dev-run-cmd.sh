project_name=backrest

if [ ! -d /var/run/$project_name ]; then
  sudo mkdir -p /var/run/$project_name
  sudo chown $USER:$project_name /var/run/$project_name
fi

python3 backrest-cmd.py
