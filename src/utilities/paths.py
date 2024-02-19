import os


def remove_path_prefix(path: str, prefix: str) -> str:
    # turn both into absolute paths
    path = os.path.abspath(path)
    prefix = os.path.abspath(prefix)
    # remove the prefix
    if path.startswith(prefix):
        return path[len(prefix) :]
    return path


def add_path_to_prefix(prefix: str, path: str):
    if path.startswith("/"):
        return os.path.join(prefix, path[1:])
    return os.path.join(prefix, path)
