from backrest_cmd.config.config import Config
import os
import yaml


class YamlConfig(Config):
    def value(self, key):        
        with open(self.config_path, 'r') as file:
            config = yaml.safe_load(file)
            value = config.get(key)
            if value is None:
                return None
            if value.lower() == 'true' or value == '1' or value:
                return '1'                        
        return value

    def validate_config_file(self):        
        if not os.path.exists(self.config_path):
            try:
                self.create_config_file()
            except Exception:
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