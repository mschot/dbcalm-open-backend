from backrest.data.model.backup import Backup
from backrest.data.model.process import Process
from backrest.data.adapter.adapter_factory import adapter_factory as data_adapter_factory


def process_to_backup(process: Process) -> Backup:
    if process.type != 'backup':
        raise ValueError("Process type must be 'backup'")
    
    if not process.args.get('identifier'):
        raise ValueError("Process must have an identifier")
    
    identifier = process.args.get('identifier')
    if data_adapter_factory().get(Backup, {'identifier': identifier}):
        raise ValueError("Backup with identifier %s already exists and has to be unique" % identifier)
    
    from_identifier = process.args.get('from_identifier') if process.args.get('from_identifier') else None

    return Backup(
        identifier=process.args.get('identifier'),
        from_identifier=from_identifier,
        start_time=process.start_time,
        end_time=process.end_time
    )