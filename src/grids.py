from abc import ABC, abstractmethod
from .motor_grid_control import Motors_Control, cart2pol
from .config import Circular_constant_density_config
import numpy as np
import logging

log = logging.getLogger(__name__)

class Grid(ABC):
    @abstractmethod
    def make_grid(self) -> None:
        pass

    def validate_grid(self, motors_controller: Motors_Control) -> None:
        log.debug(f"{self.__class__.__name__}: Validating grid elements...")
        self.valid_mask = []
        for (x, y) in self.grid_positions:
            self.valid_mask.append(motors_controller.dummy_check_PMT_curvature(x, y))
        self.valid_grid_positions = np.array(self.grid_positions)[self.valid_mask]
        log.debug(f"{self.__class__.__name__}: Finished validating grid elements...")

class Circular_Constant_Density(Grid):
    def __init__(self, cfg: Circular_constant_density_config) -> None:
        log.debug(f"Instance of {self.__class__.__name__} created")
        self.max_R = cfg.r_max
        self.step = cfg.r_step

    def _dummy_square_grid(self) -> None:
        self.xy_sq = np.arange(0, self.max_R + self.step, self.step)
        self.xy_sq = np.unique(np.append(-self.xy_sq, self.xy_sq))

    def make_grid(self) -> None:
        log.debug(f"{self.__class__.__name__}: Building grid...")
        self._dummy_square_grid()
        self.grid_positions = []
        for x in self.xy_sq:
            for y in self.xy_sq:
                r, phi = cart2pol(x, y)
                if r <= self.max_R:
                    self.grid_positions.append([x, y])
        log.debug(f"{self.__class__.__name__}: Finished building grid...")





