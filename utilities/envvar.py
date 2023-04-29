import os
from typing import Optional


def get_env_vars() -> dict:
    return dict(os.environ)


def get_env_var(key: str) -> Optional[str]:
    return os.getenv(key)


def get_env_var_with_default(key: str, default_value: str) -> str:
    return os.getenv(key, default_value)
