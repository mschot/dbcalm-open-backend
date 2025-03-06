from sqlmodel import SQLModel


def has_attributes_for_dict_keys(model: SQLModel, value: dict) -> bool:
    keys = value.keys()
    return all(hasattr(model, key) for key in keys)
