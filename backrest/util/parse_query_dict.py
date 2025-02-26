
def parse_query_dict(dict_str: str) -> dict:
    query_dict = {}
    if not dict_str:
        return query_dict

    for pair in dict_str.split(","):
        key, value = pair.split(":")
        query_dict[key] = value
    return query_dict
