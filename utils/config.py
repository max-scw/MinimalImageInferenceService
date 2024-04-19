from pathlib import Path
import tomllib

import logging
import sys

from typing import Union

from utils import (
    get_environment_variables,
    get_env_variable,
    cast_logging_level
)


def load_default_config(path_to_config: Union[str, Path]) -> dict:
    with open(Path(path_to_config), "rb") as fid:
        config_default = tomllib.load(fid)
    config_default_env = dict()

    for group in config_default:
        for ky, vl in config_default[group].items():
            # variable name
            var_nm = "_".join([group, ky]).upper()
            # nm = "_".join([prefix, var_nm]).upper()
            config_default_env[var_nm] = vl if vl else None
    return config_default_env


def get_config(default_prefix: str) -> dict:
    # --- load default config
    default_config = Path("./default_config.toml")
    if default_config.is_file():
        config_default = load_default_config(default_config)
    else:
        config_default = dict()

    # get custom config
    prefix = get_env_variable("PREFIX", default_prefix)
    config_environment_vars = get_environment_variables(rf"{prefix}_" if prefix else "", False)

    # merge configs
    config = config_default | config_environment_vars

    # set logging
    logging.basicConfig(
        level=cast_logging_level(get_env_variable("LOGGING_LEVEL", None)),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            # logging.FileHandler(Path(get_env_variable("LOGFILE", "log")).with_suffix(".log")),
            logging.StreamHandler(sys.stdout)
        ],
    )
    return config
