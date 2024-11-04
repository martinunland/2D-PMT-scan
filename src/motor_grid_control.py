import asyncio
from typing import Callable
import numpy as np
import logging
from .config import MotorConfig
from scanner_motor_control import ScannerControl

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
    async def move_to_absolute_position_in_mm(self,position):
        await asyncio.sleep(0.5)
        pass
    def check_position_in_mm_allowed(self, position):
        return [True,True,True]
    def connect(self):
        pass
    def configure_motors(self):
        pass

class MotorsControl:
    def __init__(self, cfg: MotorConfig) -> None:
        self.cfg = cfg
        self.make_distance_correction_callable()

        self.second_pmt_position = [1, 1, 1]
        self.diode_position = [1, 1, 1]
        self.PMT_centre = np.array([1, 1, 1])
        self.last_set_coordinates = [-1, -1]
        self.mot = DummyMotorScas()

    def make_distance_correction_callable(self):
        try:
            x, y = np.loadtxt(self.cfg.PMT_curvature_mapping, unpack=1)
            from scipy.interpolate import interp1d
            self.f_distance_correction = interp1d(x,y)
        except Exception as err:
            log.error(f"Error of type {type(err).__name__}: {err}")
            log.warning("Loading file with PMT curvature mapping failed, no curvature correction will be performed!...")
            self.f_distance_correction = lambda x: x

    def get_current_position(self):
        return [1,1,1]

    async def connect_and_configure(self) -> None:
        log.info("Connecting to motors async...")
        self.mot.connect()
        self.mot.configure_motors()

    def dummy_check_PMT_curvature(self, x, y):
        r, phi = cart2pol(x,y)
        rel_pos_polar = np.append(
            self.f_distance_correction(r), pol2cart(r, np.deg2rad(phi))
        )
        abs_pos_cart = self.PMT_centre + rel_pos_polar
        if not self.check_position(abs_pos_cart):
            return False
        return True
        

    def _make_absolute_position(self, x, y):
        r, phi = cart2pol(x,y)
        rel_pos_polar = np.append(
            self.f_distance_correction(r), pol2cart(r, np.deg2rad(phi))
        )
        abs_pos_cart = self.PMT_centre + rel_pos_polar
        return abs_pos_cart

    def _make_absolute_position_polar(self, r,phi):
        rel_pos_polar = np.append(
            self.f_distance_correction(r), pol2cart(r, np.deg2rad(phi))
        )
        abs_pos_cart = self.PMT_centre + rel_pos_polar
        return abs_pos_cart 

    async def check_PMT_curvature_and_move(self, x, y):
        log.info(f"Moving to x={x:.2f}, y={y:.2f}")
        abs_pos_cart = self._make_absolute_position(x,y)
        if not self.check_position(abs_pos_cart):
            log.warning(
                "Skipping position %s since it is out of boundaries", abs_pos_cart
            )
            return False
        self.last_set_coordinates = list(abs_pos_cart)
        await self.mot.move_to_absolute_position_in_mm(list(abs_pos_cart))
        return True

    async def check_PMT_curvature_and_move_polar(self, r, phi):
        abs_pos_cart = self._make_absolute_position_polar(r,phi)
        if not self.check_position(abs_pos_cart):
            log.warning(
                "Skipping position %s since it is out of boundaries", abs_pos_cart
            )
            return False
        log.info(f"Moving to R={r:.2f}, phi={phi:.2f}, ({abs_pos_cart})")
        self.last_set_coordinates = list(abs_pos_cart)
        await self.mot.move_to_absolute_position_in_mm(list(abs_pos_cart))
        return True

    def check_position(self, position):
        """Returns false if position is outside the boundaries of any of the motors."""
        return all(self.mot.check_position_in_mm_allowed(position))

    def check_position_polar(self, r, phi):
        """Returns false if position is outside the boundaries of any of the motors."""
        abs_pos_cart = self._make_absolute_position_polar(r, phi)
        return all(self.mot.check_position_in_mm_allowed(abs_pos_cart))

    async def move_to_second_PMT(self):
        log.info(f"Moving to second pmt position x={self.second_pmt_position[2]:.2f}, y={self.second_pmt_position[1]:.2f}")
        valid = self.check_position(self.second_pmt_position)
        if valid:
            await self.mot.move_to_absolute_position_in_mm(self.second_pmt_position)
        else:
            raise ValueError(
                "Second PMT position is out of motor boundaries (%s)! Configure a valid position, or deactivate reference measurement",
                self.second_pmt_position,
            )

    async def move_to_diode(self):
        log.info(f"Moving to diode position x={self.diode_position[2]:.2f}, y={self.diode_position[1]:.2f}")
        valid = self.check_position(self.diode_position)
        if valid:
            await self.mot.move_to_absolute_position_in_mm(self.diode_position)
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