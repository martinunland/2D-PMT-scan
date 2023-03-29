import logging
import os
import pathlib
from enum import Enum
import time

class MeasurementMode(Enum):
    PULSE = "pulse"
    CURRENT = "current"

def add_spam_log_level():
    DEBUG_LEVELV_NUM = 1
    logging.addLevelName(DEBUG_LEVELV_NUM, "SPAM")

    def spam(self, message, *args, **kws):
        if self.isEnabledFor(DEBUG_LEVELV_NUM):
            # Yes, logger takes its '*args' as 'args'.
            self._log(DEBUG_LEVELV_NUM, message, args, **kws)

    logging.Logger.spam = spam

def get_hydra_working_directory()-> pathlib.Path:
    from hydra.core.hydra_config import HydraConfig
    return pathlib.Path(HydraConfig.get().runtime.output_dir)


def make_folder_in_working_directory(folder: str) -> pathlib.Path:
    hydrawd = get_hydra_working_directory()
    newfolder = hydrawd.joinpath(folder)
    if not os.path.exists(newfolder):
        os.mkdir(newfolder)
    return newfolder


        