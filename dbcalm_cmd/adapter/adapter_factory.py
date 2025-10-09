from dbcalm_cmd.adapter.adapter import Adapter
from dbcalm_cmd.adapter.system_commands import SystemCommands
from dbcalm_cmd.process.runner_factory import runner_factory


def adapter_factory() -> Adapter:
    return SystemCommands(runner_factory())
