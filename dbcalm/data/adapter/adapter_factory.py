from dbcalm.config.config_factory import config_factory
from dbcalm.data.adapter.adapter import Adapter
from dbcalm.data.adapter.local import Local


def adapter_factory() -> Adapter:
    config = config_factory()
    if config.value("service") is None or config.value("service") == "sqlite":
        return Local()
    msg = "Invalid adapter type"
    raise ValueError(msg)




