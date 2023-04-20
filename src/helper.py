import logging
import os
import pathlib
from enum import Enum
import time


class MeasurementMode(Enum):
    PULSE = "pulse"
    CURRENT = "current"


def get_hydra_working_directory() -> pathlib.Path:
    from hydra.core.hydra_config import HydraConfig

    return pathlib.Path(HydraConfig.get().runtime.output_dir)


def make_folder_in_working_directory(folder: str) -> pathlib.Path:
    hydrawd = get_hydra_working_directory()
    newfolder = hydrawd.joinpath(folder)
    if not os.path.exists(newfolder):
        os.mkdir(newfolder)
    return newfolder
