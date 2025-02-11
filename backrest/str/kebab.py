import re

def kebab_case(s):
    s = s.lower()  # Convert to lowercase first
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')  # Replace non-alphanumeric with "-" and remove leading/trailing "-"
