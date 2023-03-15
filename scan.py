from typing import Tuple
from src.scan import Scan_Manager
from src.DAQ import DAQ_Device, TestOsci, TestPicoamp
from src.grids import Circular_Constant_Density
from src.config import Measurement_Config, DAQ_config
from src.motor_grid_control import Motors_Control, Coils_dummy
from src.data_analysis import Pulse_Mode_Analysis, Current_Mode_Analysis
from hydra.core.config_store import ConfigStore
from hydra.core.hydra_config import HydraConfig
import hydra
import logging
import asyncio
log = logging.getLogger(__name__)

def init_pulse_mode_scan(motors: Motors_Control, cfg: DAQ_config)->Tuple[Pulse_Mode_Analysis, DAQ_Device]:
    motors.set_default_reference_callable(motors.move_to_second_PMT)
    analyser = Pulse_Mode_Analysis(cfg.picoscope)
    daq = TestOsci()
    return analyser, daq

def init_current_mode_scan(motors: Motors_Control, cfg: DAQ_config)->Tuple[Current_Mode_Analysis, DAQ_Device]:
    motors.set_default_reference_callable(motors.move_to_diode)
    analyser = Current_Mode_Analysis(cfg.picoamp)
    daq = TestPicoamp()
    return analyser, daq


async def run_measurement(cfg: Measurement_Config)-> None:
    motors = Motors_Control(cfg.cfg_motors)
    coils = Coils_dummy()
    analyser, daq = init_pulse_mode_scan(motors, cfg.cfg_DAQ)
    await asyncio.gather(motors.connect_and_configure(), coils.connect_and_configure(), daq.connect())
    
    grid = Circular_Constant_Density(cfg.cfg_grid)
    grid.make_grid()
    grid.validate_grid(motors)

    # analyser, daq = init_pulse_mode_scan(motors ,cfg.cfg_DAQ)
    # scan_manager = Scan_Manager(grid=grid, motors=motors, device=daq, analyser=analyser)
    # scan_manager.run()

# * Configstore is the convoluted way of hydra to pass the config file data to a dataclass structure
cs = ConfigStore.instance()
cs.store(name="measurement_config", node=Measurement_Config)

@hydra.main(
    config_path="config", config_name="config", version_base=None
)  # * hydra passes the configuration file config_name in config_path to the input cfg in main function
def run_scan(cfg: Measurement_Config) -> None:
    asyncio.run(run_measurement(cfg))

if __name__ == "__main__":
    run_scan()
