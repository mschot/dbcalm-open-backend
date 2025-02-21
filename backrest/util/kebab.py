import re


def kebab_case(s: str) -> str:
    # Convert to lowercase first
    s = s.lower()
    # Replace non-alphanumeric with "-" and remove leading/trailing "-"
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")
