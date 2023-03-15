from src.scan import Scan_Manager
from src.DAQ import TestOsci, TestPicoamp
from src.grids import Circular_Constant_Density
from src.config import Measurement_Config
from src.motor_grid_control import Motors_Control
from src.data_analysis import Pulse_Mode_Analysis, Current_Mode_Analysis
from hydra.core.config_store import ConfigStore
from hydra.core.hydra_config import HydraConfig
import hydra
import logging
log = logging.getLogger(__name__)

def init_pulse_mode_scan():
    analyser = Pulse_Mode_Analysis()
    daq = TestOsci()
    return analyser, daq

def init_current_mode_scan():
    analyser = Current_Mode_Analysis()
    daq = TestPicoamp()
    return analyser, daq

# * Configstore is the convoluted way of hydra to pass the config file data to a dataclass structure
cs = ConfigStore.instance()
cs.store(name="measurement_config", node=Measurement_Config)

@hydra.main(
    config_path="config", config_name="config", version_base=None
)  # * hydra passes the configuration file config_name in config_path to the input cfg in main function
def main(cfg: Measurement_Config) -> None:
    print(cfg.cfg_DAQ)
    grid = Circular_Constant_Density(cfg.cfg_grid)
    grid.make_grid()

    motors = Motors_Control(cfg.cfg_motors)

    analyser, daq = init_pulse_mode_scan()
    
    scan_manager = Scan_Manager(grid=grid, motors=motors, device=daq, analyser=analyser)
    pass


if __name__ == "__main__":
    main()
