from dbcalm.config.config_factory import config_factory
from dbcalm_mariadb_cmd.adapter.adapter import Adapter
from dbcalm_mariadb_cmd.adapter.mariadb_factory import mariadb_factory
from dbcalm_mariadb_cmd.adapter.mysql_factory import mysql_factory


def adapter_factory() -> Adapter:
    config = config_factory()
    db_type = config.value("db_type")
    if db_type == "mariadb":
        return mariadb_factory(config)
    if db_type == "mysql":
        return mysql_factory(config)
    msg = f"Invalid db_type: {db_type}. Supported types: mariadb, mysql"
    raise ValueError(msg)




