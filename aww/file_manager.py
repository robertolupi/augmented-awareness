import os
from datetime import datetime


def read_file_content(filepath):
    """Reads the content of a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def get_file_paths(dir1, dir2, level, selected_date):
    year = selected_date.year
    month = selected_date.strftime("%m")
    day = selected_date.strftime("%d")
    week = selected_date.strftime("%W")

    if level == "daily":
        path = os.path.join(str(year), month, f"r{year}-{month}-{day}.md")
    elif level == "weekly":
        path = os.path.join(str(year), "weeks", f"r{year}-W{week}.md")
    elif level == "monthly":
        path = os.path.join(str(year), "months", f"r{year}-{month}.md")
    elif level == "yearly":
        path = os.path.join(str(year), f"r{year}.md")
    else:
        return None, None

    return os.path.join(dir1, path), os.path.join(dir2, path)
