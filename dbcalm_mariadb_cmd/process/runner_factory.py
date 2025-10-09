from dbcalm_mariadb_cmd.process.runner import Runner


def runner_factory() -> Runner:
    return Runner()
