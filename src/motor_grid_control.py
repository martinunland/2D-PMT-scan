from typing import Callable
import numpy as np

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


class Motors_Control:
    def __init__(self, f_distance_correction: Callable) -> None:
        self.mot = None
        self.second_pmt_position = [-1, -1, -1]
        self.diode_position = [-1, -1, -1]
        self.PMT_centre = np.array([-1, -1, -1])
        self.f_distance_correction = f_distance_correction
        self.last_set_coordinates = [-1, -1]

    def connect_and_configure_motors(self) -> None:
        pass

    def dummy_check_PMT_curvature(self, x, y):
        rel_pos_polar = np.append(
            self.f_distance_correction(r), pol2cart(r, np.deg2rad(phi))
        )
        abs_pos_cart = self.PMT_centre + rel_pos_polar
        if not self.check_position(abs_pos_cart):
            return False
        return True

    async def check_PMT_curvature_and_move(self, x, y):
        logging.debug("Moving to x = " + str(round(x, 2)) + ", y=" + str(round(y, 2)))
        rel_pos_polar = np.append(
            self.f_distance_correction(r), pol2cart(r, np.deg2rad(phi))
        )
        abs_pos_cart = self.PMT_centre + rel_pos_polar

        if not self.check_position(abs_pos_cart):
            logging.info(
                "Skipping position %s since it is out of boundaries", abs_pos_cart
            )
            return False
        self.last_set_coordinates = [x, y]
        await self.mot.Move_3d_in_mm(list(abs_pos_cart), 0)
        return True

    def check_position(self, position):
        for val in position:
            if val >= self.mot.max_absolute_step or val < self.mot.min_absolute_step:
                return False
        return True

    async def move_to_second_PMT(self):
        valid = self.check_position(self.second_pmt_position)
        if valid:
            await self.mot.Move_3d_in_mm(self.second_pmt_position, 0)
        else:
            raise ValueError(
                "Second PMT position is out of motor boundaries (%s)! Configure a valid position, or deactivate reference measurement",
                self.second_pmt_position,
            )

    async def move_to_diode(self):
        valid = self.check_position(self.diode_position)
        if valid:
            await self.mot.Move_3d_in_mm(self.diode_position, 0)
        else:
            raise ValueError(
                "Diode position is out of motor boundaries (%s)! Configure a valid position, or deactivate reference measurement",
                self.diode_position,
            )