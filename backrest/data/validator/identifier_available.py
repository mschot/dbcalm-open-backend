from backrest.data.adapter.adapter_factory import adapter_factory as data_adapter_factory
import os

def identifier_available(identifier, data_adapter, backup_dir):

    data_adapter = data_adapter_factory()
    # Check in data adapter
    if data_adapter.exists(identifier):
        return False

    # Check in backup directory
    backup_path = os.path.join(backup_dir, identifier)
    if os.path.exists(backup_path):
        return False

    return True