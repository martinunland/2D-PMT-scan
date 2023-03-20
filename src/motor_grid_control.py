import asyncio
from typing import Callable
import numpy as np
import logging
from .config import MotorConfig

log = logging.getLogger(__name__)

def cart2pol(x, y):
    rho = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y, x)
    return (rho, np.rad2deg(phi))


def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return (y, x)


def distance_between_two_points(p1, p2):
    vals = 0
    for k, l in zip(p1, p2):
        vals += (k - l) ** 2
    return np.sqrt(vals)

class DummyMotors:
    def __init__(self):
        self.min_absolute_position = 0
        self.max_absolute_position = 205
    async def Move_3d_in_mm(self,position, relative):
        await asyncio.sleep(0.5)
        pass

class MotorsControl:
    def __init__(self, cfg: MotorConfig) -> None:

        
        self.cfg = cfg
        self.make_distance_correction_callable()

        self.second_pmt_position = [1, 1, 1]
        self.diode_position = [1, 1, 1]
        self.PMT_centre = np.array([1, 1, 1])
        self.last_set_coordinates = [-1, -1]

    def make_distance_correction_callable(self):
        try:
            x, y = np.loadtxt(self.cfg.PMT_curvature_mapping, unpack=1)
            from scipy.interpolate import interp1d
            self.f_distance_correction = interp1d(x,y)
        except Exception as err:
            log.error(err)
            log.warning("Loading file with PMT curvature mapping failed, no curvature correction will be performed!...")
            self.f_distance_correction = lambda x: x

    def get_current_position(self):
        return [1,1,1]

    async def connect_and_configure(self) -> None:
        self.mot = DummyMotors()
        log.info("Connecting to motors...")
        await asyncio.sleep(0.5)
        log.info("Motors connected!")

    def dummy_check_PMT_curvature(self, x, y):
        r, phi = cart2pol(x,y)
        rel_pos_polar = np.append(
            self.f_distance_correction(r), pol2cart(r, np.deg2rad(phi))
        )
        abs_pos_cart = self.PMT_centre + rel_pos_polar
        if not self.check_position(abs_pos_cart):
            return False
        return True

    async def check_PMT_curvature_and_move(self, x, y):
        log.info(f"Moving to x={x:.2f}, y={y:.2f}")

        r, phi = cart2pol(x,y)
        rel_pos_polar = np.append(
            self.f_distance_correction(r), pol2cart(r, np.deg2rad(phi))
        )
        abs_pos_cart = self.PMT_centre + rel_pos_polar

        if not self.check_position(abs_pos_cart):
            log.warning(
                "Skipping position %s since it is out of boundaries", abs_pos_cart
            )
            return False
        self.last_set_coordinates = [x, y]
        await self.mot.Move_3d_in_mm(list(abs_pos_cart), 0)
        return True

    def check_position(self, position):
        for val in position:
            if val >= self.mot.max_absolute_position or val < self.mot.min_absolute_position:
                return False
        return True

    async def move_to_second_PMT(self):
        log.info(f"Moving to second pmt position x={self.second_pmt_position[2]:.2f}, y={self.second_pmt_position[1]:.2f}")
        valid = self.check_position(self.second_pmt_position)
        if valid:
            await self.mot.Move_3d_in_mm(self.second_pmt_position, 0)
        else:
            raise ValueError(
                "Second PMT position is out of motor boundaries (%s)! Configure a valid position, or deactivate reference measurement",
                self.second_pmt_position,
            )

    async def move_to_diode(self):
        log.info(f"Moving to diode position x={self.diode_position[2]:.2f}, y={self.diode_position[1]:.2f}")
        valid = self.check_position(self.diode_position)
        if valid:
            await self.mot.Move_3d_in_mm(self.diode_position, 0)
        else:
            
            raise ValueError(
                "Diode position is out of motor boundaries (%s)! Configure a valid position, or deactivate reference measurement",
                self.diode_position,
            )
    
    async def move_to_reference(self):
        await self._reference_callable()

    def set_default_reference_callable(self, f: Callable):
        self._reference_callable = f



class CoilsDummy:
    def __init__(self):
        pass
    async def connect_and_configure(self):
        log.info("Connecting to coils...")
        await asyncio.sleep(1.75)
        log.info("Coils connected!")