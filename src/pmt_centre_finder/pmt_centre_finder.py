import logging
from typing import Tuple
import numpy as np
from src.DAQ import DAQDevice
from src.motor_grid_control import MotorsControl
from src.data_analysis import DataAnalysis
from src.config import CentreFindConfig
from .minimiser import PMT_circle_fitting
from alive_progress import alive_bar
from src.helper import make_folder_in_working_directory

log = logging.getLogger(__name__)

class CentreFinder:
    def __init__(self, cfg: CentreFindConfig, motors: MotorsControl, analyser: DataAnalysis, daq: DAQDevice):

        self.cfg = cfg
        self.analyser = analyser
        self.motors = motors
        self.daq = daq
        self.save_path = make_folder_in_working_directory("centre_finder_output")

    async def measure_intensity(self)->Tuple[float,float]:
        data, timestamp = await self.daq.read()
        (intensity, error), _ = self.analyser.get_simple_intensity(data)
        return intensity, error

    async def prompt_to_user(self):
        log.warning("You want to find the centre of the PMT!")
        log.warning("For this to work you have to make an effort and place the fibre already near the PMT centre (at least within ~10-20mm)...")
        log.warning("If this is already the case, write q/Q. Otherwise, feed me with (x,y,z) values until you think it is around the centre")
        log.critical("Be careful, I can't attemp avoiding collisions during this!")
        await self._input_user_value()

    async def _input_user_value(self):
        log.warning("Enter three values, separated by spaces, or y/Y")
        while True:
            self._warn_current_position()
            user_input = input("x y z or q/Q:")
            if "q" in user_input or "Q" in user_input:
                return 
            try:
                x, y, z = user_input.split()
                x, y, z = float(x), float(y), float(z)
                await self.motors.mot.move_to_absolute_position_in_mm([x, y, z])

            except ValueError as err:
                log.error("You have to provide 3 numbers separated by a space, or q to quit!")

    def _warn_current_position(self):
        x,y,z = self.motors.get_current_position()
        log.warning(f"Current position x: {x:.2f}, y: {y:.2f}, z: {z:.2f}")


    async def measure_background_threshold(self, factor:float = 3):
        """Move the fibre to a location where PMT is not illuminated and measure the background level. The threshold for signal is set as factor*background.
        Args:
            factor (default 3)
        """
        #Look for a radius/angle pair that is within motor volume
        for radius in np.arange(self.cfg.PMT_bulb_radius+10, self.cfg.PMT_bulb_radius+5, -1):
            for phi in np.arange(0,360,1):
                if self.motors.check_position_polar(radius, phi):
                    break
        await self.motors.check_PMT_curvature_and_move_polar(radius, phi)
        self.threshold = await self.measure_intensity()
        self.threshold = self.threshold[0]*factor

    async def measure_profile(self, angle):
        #start far away from PMT taking into account beam diameter
        current_R = self.cfg.profile_r_start
        await self.motors.check_PMT_curvature_and_move_polar(current_R, angle)
        
        intensity = await self.measure_intensity()

        if intensity[0]>self.threshold:
            log.info(f"Skipping profile along angle {angle}; first value already over threshold...")
            log.info("If you keep getting this message, run CentreFinder.measure_background_threshold(factor) again with a larger factor")
            return
        
        not_in_cathode = True
        intensities = []
        intensities_e = []
        position = []
        position_R = []
        step = -self.cfg.coarse_step
        while True:
            current_position = self.motors.get_current_position()
            intensity = await self.measure_intensity()
            log.info(f"Intensity at R {current_R:.1f}, phi {angle:.1f}: {intensity[0]:.3g}+-{intensity[1]:.3g}")   
            intensities.append(intensity[0]) 
            intensities_e.append(intensity[1]) 
            position.append(current_position) 
            position_R.append(current_R)

            if not_in_cathode and np.abs(intensity[0])>self.threshold:
                current_R += self.cfg.mid_step
                step = -self.cfg.fine_step
                not_in_cathode = False
            else:
                current_R += step
            if current_R < self.cfg.profile_r_stop:
                break
            await self.motors.check_PMT_curvature_and_move_polar(current_R, angle)
                
        return(np.array(intensities), np.array(intensities_e), np.array(position), np.array(position_R))



    async def measure_all_profiles(self):
        np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)
        self.all_profile_angles = np.arange(0,360, self.cfg.ang_step)

        await self.motors.check_PMT_curvature_and_move_polar(0,0)
        centre_intensity = await self.measure_intensity()

        with alive_bar(self.all_profile_angles.size, enrich_print = False, title="Measuring profiles") as bar:
            for angle in self.all_profile_angles:
                try:
                    intensity, intensity_error, positions, Rs = await self.measure_profile(angle)
                    np.save(self.save_path / f"profile_{angle}deg.npy", (intensity, intensity_error, positions, Rs, centre_intensity, self.threshold))
                    bar()
                except Exception as err:
                    log.error(err)
                    bar(skipped=True)
                    continue
                

    def analyse_profiles(self):
        fitter = PMT_circle_fitting(self.cfg.PMT_bulb_radius, self.motors.PMT_centre, self.save_path, self.all_profile_angles)
        (x0, x0_err), (y0, y0_err) = fitter.fit_profiles_and_get_PMT_centre()


    async def run(self):
        await self.daq.configure_for_primary()
        await self.prompt_to_user()
        await self.measure_background_threshold()
        await self.measure_all_profiles()
        self.analyse_profiles()
