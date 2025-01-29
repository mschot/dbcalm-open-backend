import os
import yaml


class Config:
    project_name = 'backrest'
    
    def __init__(self):
        self.config_path = '/etc/'+ self.project_name + '/config.yml'   

    def value(self, key):        
        with open(self.config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config[key]

    def validate_config_file(self):        
        if not os.path.exists(self.config_path):
            try:
                self.create_config_file()
            except Exception as e:
                raise Exception(f"Configuration file could not be created: {self.config_path} run the command with sudo")
        
        with open(self.config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        required_params = ['dbtype', 'username', 'password', 'host']
        for param in required_params:
            if param not in config:
                raise ValueError(f"Missing required parameter: {param}")
        
        return config
    
    def create_config_file(self):
        if os.path.exists(self.config_path):
            return print(f"Configuration file already exists: {self.config_path}")

        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        config = self.config_template()
        with open(self.config_path, 'w') as file:
            yaml.dump(config, file)
        
        return config
    
    def config_template(self):
        return {
            'dbtype': 'mariadb',
            'username': 'admin',
            'password': 'admin',
            'host': 'localhost',
            'backup_path': '/var/lib/backrest/backups',
        }