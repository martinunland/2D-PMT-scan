import os
from typing import Tuple
from src.scan_manager import ScanManager
from src.DAQ import DAQDevice, TestOsci, TestPicoamp
from src.grids import CircularConstantDensity
from src.config import MeasurementConfig, DAQConfig
from src.motor_grid_control import MotorsControl, CoilsDummy
from src.data_analysis import PulseModeAnalysis, CurrentModeAnalysis
from hydra.core.config_store import ConfigStore
import hydra
import logging
import asyncio
from src.helper import add_spam_log_level 

add_spam_log_level()
log = logging.getLogger(__name__)

def init_pulse_mode_scan(motors: MotorsControl, cfg: DAQConfig)->Tuple[PulseModeAnalysis, DAQDevice]:
    motors.set_default_reference_callable(motors.move_to_second_PMT)
    analyser = PulseModeAnalysis(cfg.picoscope)
    daq = TestOsci()
    return analyser, daq

def init_current_mode_scan(motors: MotorsControl, cfg: DAQConfig)->Tuple[CurrentModeAnalysis, DAQDevice]:
    motors.set_default_reference_callable(motors.move_to_diode)
    analyser = CurrentModeAnalysis(cfg.picoamp)
    daq = TestPicoamp()
    return analyser, daq


async def run_measurement(cfg: MeasurementConfig)-> None:
    motors = MotorsControl(cfg.cfg_motors)
    coils = CoilsDummy()
    analyser, daq = init_pulse_mode_scan(motors, cfg.cfg_DAQ)
    await asyncio.gather(motors.connect_and_configure(), coils.connect_and_configure(), daq.connect())
    
    grid = CircularConstantDensity(cfg.cfg_grid)
    grid.make_grid()
    grid.validate_grid(motors)

    analyser, daq = init_pulse_mode_scan(motors ,cfg.cfg_DAQ)
    scan_manager = ScanManager(grid=grid, motors=motors, device=daq, analyser=analyser, cfg=cfg.cfg_statistics)
    await scan_manager.run()

# * Configstore is the convoluted way of hydra to pass the config file data to a dataclass structure
cs = ConfigStore.instance()
cs.store(name="measurement_config", node=MeasurementConfig)


@hydra.main(
    config_path="config", config_name="config", version_base=None
)  # * hydra passes the configuration file config_name in config_path to the input cfg in main function
def run_scan(cfg: MeasurementConfig) -> None:
    asyncio.run(run_measurement(cfg))

if __name__ == "__main__":
    run_scan()
