import os

# TODO
# class RelativeFilePath:


def standardize_code_path(path: str) -> str:
    path = path.replace("\\", "/")
    if path.startswith("/"):
        return path[1:]
    return path


def remove_path_prefix(path: str, prefix: str) -> str:
    # turn both into absolute paths
    path = os.path.abspath(path)
    prefix = os.path.abspath(prefix)
    # remove the prefix
    if path.startswith(prefix):
        return path[len(prefix) :]
    return path


def add_path_to_prefix(prefix: str, path: str):
    return os.path.join(prefix, standardize_code_path(path))
