from pathlib import Path
import tomllib
import re

import logging
import sys

from typing import Union

from utils import (
    get_environment_variables,
    get_env_variable,
    cast_logging_level
)


def set_logging():
    log_file = get_env_variable("LOGFILE", None)
    logging.basicConfig(
        level=cast_logging_level(get_env_variable("LOGGING_LEVEL", logging.INFO)),
        format="%(asctime)s [%(levelname)s] %(message)s",
        # handlers=[logging.StreamHandler(sys.stdout)] +
        #          [logging.FileHandler(Path(log_file).with_suffix(".log"))] if log_file is not None else [],
    )


re_replace = re.compile("[^a-zA-Z0-9]")
def load_default_config(path_to_config: Union[str, Path]) -> dict:
    with open(Path(path_to_config), "rb") as fid:
        config_default = tomllib.load(fid)

    def flatten_dictionary(dictionary: dict, key: str = None) -> dict:
        variables = dict()
        for ky, vl in dictionary.items():
            # variable name
            var_nm = ((f"{key}_" if key else "") + f"{ky}").upper()
            # ensure that the variables names are only characters, digits, or underscores, i.e. variable names in python
            var_nm = re_replace.sub("_", var_nm)
            # recursion
            if isinstance(vl, dict):
                variables |= flatten_dictionary(vl, var_nm)
            else:
                variables[var_nm] = vl
        return variables

    return flatten_dictionary(config_default)


def get_config(default_prefix: str = "") -> dict:
    # --- load default config
    default_config = Path("./default_config.toml")
    if default_config.is_file():
        config_default = load_default_config(default_config)
    else:
        config_default = dict()

    # prefix of the environment variables
    prefix = default_prefix
    if not default_prefix:
        if "PREFIX" in config_default:
            prefix = config_default["PREFIX"]
        elif "GENERAL_PREFIX" in config_default:
            prefix = config_default["GENERAL_PREFIX"]

    # get overwrite default config with environment variables
    prefix = get_env_variable("PREFIX", prefix)
    config_environment_vars = get_environment_variables(rf"{prefix}_" if prefix else "", False)

    # merge configs
    config = config_default | config_environment_vars

    # set logging
    set_logging()
    logging.debug(f"Configuration: {config}")
    return config
