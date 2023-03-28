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

def get_hydrawd()-> pathlib.Path:
    if "HYDRA_OUTPUT_DIR" in os.environ:
        from hydra.core.hydra_config import HydraConfig
        return pathlib.Path(HydraConfig.get().runtime.output_dir)
    else: #Only needed for unittests... otherwise hydra should be always running
        return pathlib.Path(".")

def make_folder_in_hydrawd(folder: str) -> pathlib.Path:
    hydrawd = get_hydrawd()
    newfolder = hydrawd.joinpath(folder)
    if not os.path.exists(newfolder):
        os.mkdir(newfolder)
    return newfolder

class LoopTimer:
    def __init__(self, total_count:int)->None:
        self.start_time = time.time()
        self.total = total_count
        self.current_loop_count = 0

    def get_time_left(self)->float:
        self.current_loop_count+=1
        return (time.time()-self.start_time)*(self.total-self.current_loop_count)/float(self.current_loop_count)

    def print_time_left(self):
        time_left = self.get_time_left()/60. #min
        unit = "min"
        if time_left < 1:
            time_left *= 60.
            unit = "s"
        print(f"Time left:{time_left:.1f} {unit}")
        