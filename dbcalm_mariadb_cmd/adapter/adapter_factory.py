from dbcalm.config.config_factory import config_factory
from dbcalm_mariadb_cmd.adapter.adapter import Adapter
from dbcalm_mariadb_cmd.adapter.mariadb_factory import mariadb_factory


def adapter_factory() -> Adapter:
    config = config_factory()
    if config.value("db_type") == "mariadb":
        return mariadb_factory(config)
    msg = "Invalid adapter type"
    raise ValueError(msg)




