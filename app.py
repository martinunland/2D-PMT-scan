from src.scan import Scan_Manager
from src.grids import Circular_Constant_Density
from src.config import Measurement_Config
from hydra.core.config_store import ConfigStore
from hydra.core.hydra_config import HydraConfig
import hydra
import logging
log = logging.getLogger(__name__)

# * Configstore is the convoluted way of hydra to pass the config file data to a dataclass structure
cs = ConfigStore.instance()
cs.store(name="measurement_config", node=Measurement_Config)


@hydra.main(
    config_path="config", config_name="config", version_base=None
)  # * hydra passes the configuration file config_name in config_path to the input cfg in main function
def main(cfg: Measurement_Config) -> None:

    grid = Circular_Constant_Density(cfg.cfg_grid)
    grid.make_grid()
    
    #scan_manager = Scan_Manager(grid=grid)
    pass


if __name__ == "__main__":
    main()
