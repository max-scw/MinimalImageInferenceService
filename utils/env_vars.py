import os
import re

from typing import List, Dict, Any, Union


def camel_case_split(identifier):
    matches = re.finditer(".+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)", identifier)
    return [m.group(0) for m in matches]


def get_env_variable(key: str, default_value):
    return cast(os.environ[key]) if key in os.environ else default_value


def get_environment_variables(prefix: str, with_prefix: bool = True) -> Dict[str, Any]:
    re_prefix = re.compile(prefix)
    config = dict()
    for ky in os.environ:
        m = re_prefix.match(ky)
        if m:
            nm = ky if with_prefix else ky[m.end():]
            config[nm] = cast(os.environ[ky])
    return config


def cast(var: str) -> Union[None, int, float, str, bool]:
    """casting strings to primitive datatypes"""
    if re.match(r"[0-9.,]+$", var):
        if re.match(r"\d+$", var):  # integer
            var = int(var)
        elif re.match(r"((\d+\.(\d+)?)|(\.\d+))$", var):  # float
            var = float(var)
        elif re.match(r"((\d+,(\d+)?)|(,\d+))$", var):  # float
            var = float(var.replace(",", "."))
    elif re.match(r"(True)|(False)$", var, re.IGNORECASE):
        var = True if var[0].lower() == "t" else False
    return var
