from src.pmt_centre_finder.pmt_centre_finder import CentreFinder
from src.scan_manager import ScanManager
from src.grids import CircularConstantDensity
from src.config import MeasurementConfig
from src.motor_grid_control import MotorsControl, CoilsDummy
from hydra.core.config_store import ConfigStore
import hydra
import logging
import asyncio
from src.helper import MeasurementMode
from src.factory import DeviceFactory

log = logging.getLogger(__name__)

# These modules are very verbose, change as needed if you have a bug
logging.getLogger("pulse_mode_analysis").setLevel(logging.WARNING)


async def run_measurement(cfg: MeasurementConfig) -> None:

    mode = MeasurementMode.PULSE  # MeasurementMode.PULSE MeasurementMode.CURRENT

    motors = MotorsControl(cfg.cfg_motors)
    coils = CoilsDummy()
    analyser, daq = DeviceFactory.create_analyser_and_daq(mode, motors, cfg.cfg_DAQ)

    await asyncio.gather(
        motors.connect_and_configure(), coils.connect_and_configure(), daq.connect()
    )

    #centre_finder = CentreFinder(cfg.cfg_centre_finder, motors, analyser, daq)
    #await centre_finder.run()

    grid = CircularConstantDensity(cfg.cfg_grid)
    grid.make_grid()
    grid.validate_grid(motors)

    scan_manager = ScanManager(
        grid=grid, motors=motors, device=daq, analyser=analyser, cfg=cfg.cfg_statistics
    )
    await scan_manager.run()


# * Configstore is the convoluted way of hydra to pass the config file data to a dataclass structure
cs = ConfigStore.instance()
cs.store(name="measurement_config", node=MeasurementConfig)


@hydra.main(
    config_path="config", config_name="config", version_base=None
)  # * hydra passes the configuration file config_name in config_path to the input cfg in main function
def run_scan(cfg: MeasurementConfig) -> None:
    loop = asyncio.get_event_loop()
    tasks = asyncio.gather(run_measurement(cfg))
    try:
        loop.run_until_complete(tasks)
    except KeyboardInterrupt:
        log.info(
            "Scan stopped by user...maybe you have to press ctrl+c again depending on your system..."
        )
        tasks.cancel()
    finally:
        loop.close()


if __name__ == "__main__":
    run_scan()
