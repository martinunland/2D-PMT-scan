import logging
from typing import Tuple
import numpy as np
from DAQ import DAQDevice
from motor_grid_control import MotorsControl, pol2cart
from data_analysis import DataAnalysis
from src.config import CentreFindConfig
from minimiser import PMT_circle_fitting
from scipy.interpolate import interp1d
from helper import LoopTimer

log = logging.getLogger(__name__)




def minimizealot(angles,bsl):
    
    
    minim = PMT_circle_fitting( centre, PMT_Model=0)
    x_data = []
    y_data = []
    for angle in angles:
        try:
            if large:
                data,norm= np.load(anglefolder+"/lu_angle_"+str(int(angle))+".npy")
            else:
                data,norm= np.load(anglefolder+"/QE_angle_"+str(int(angle))+".npy")
            newpoint = get_nifty_fifty(centre, angle, data[3], data[0], rand = bsl)
            x_data.append(newpoint[1])
            y_data.append(newpoint[0])
        except Exception as err:
            print err
            pass
    plt.plot(x_data,y_data,'.')
    minim.x_data = np.array(x_data)
    minim.y_data = np.array(y_data)
    minim.minimize()
    return minim.parameter_best_fit

def getcenter(angles,baselines ):
    x0s = []
    y0s = []
    Rs = []
    for bs in baselines:
        temp = minimizealot(angles,bs)
        x0s.append(temp[0])
        y0s.append(temp[1])
        Rs.append(temp[2])
    x0s = np.array(x0s)
    y0s = np.array(y0s)
    y0s = y0s[x0s>0]
    Rs = np.array(Rs)
    Rs = Rs[x0s>0]
    baselines = baselines[x0s>0]
    x0s = x0s[x0s>0]
    plt.figure()
    plt.plot(baselines,x0s)
    plt.figure()
    plt.plot(baselines,y0s)
    plt.figure()
    plt.plot(baselines,Rs)
    return np.average(x0s),np.average(y0s),np.average(Rs), np.std(x0s), np.std(y0s), np.amin(x0s),np.amax(x0s),np.amin(y0s),np.amax(y0s)
    
class CentreFinder:
    def __init__(self, cfg: CentreFindConfig, motors: MotorsControl, analyser: DataAnalysis, daq: DAQDevice):

        self.cfg = cfg
        self.analyser = analyser
        self.motors = motors
        self.daq = self.daq
        self.daq.configure_for_primary()
        self.prompt_to_user()

    def measure_intensity(self)->Tuple[float,float]:
        return self.analyser.get_simple_intensity(self.daq.read())

    def prompt_to_user(self):
        log.warning("You want to find the centre of the PMT!")
        log.warning("For this to work you have to make an effort and place the fibre already near the PMT centre (at least within ~10-20mm)...")
        log.warning("If this is already the case, write q/Q. Otherwise, feed me with (x,y,z) values until you think it is around the centre")
        log.critical("Be careful, I can't attemp avoiding collisions during this!")
        self._input_user_value()

    def _input_user_value(self):
        log.warning("Enter three values, separated by spaces, or y/Y")
        while True:
            self._warn_current_position()
            user_input = input("x y z or q/Q:")
            if "q" in user_input or "Q" in user_input:
                return 
            try:
                x, y, z = user_input.split()
                x, y, z = float(x), float(y), float(z)
                self.motors.mot.move_to_absolute_position_in_mm([x, y, z])

            except ValueError as err:
                log.error("You have to provide 3 numbers separated by a space, or q to quit!")

    def _warn_current_position(self):
        x,y,z = self.motors.get_current_position()
        log.warning(f"Current position x: {x:.2f}, y: {y:.2f}, z: {z:.2f}")


    def measure_background_threshold(self, factor:float = 3):
        """Move the fibre to a location where PMT is not illuminated and measure the background level. The threshold for signal is set as factor*background.
        Args:
            factor (default 3)
        """
        #Look for a radius/angle pair that is within motor volume
        for radius in np.arange(self.cfg.PMT_bulb_radius+10, self.cfg.PMT_bulb_radius+5, -1):
            for phi in np.arange(0,360,1):
                if self.motors.check_position_polar(radius, phi):
                    break
        self.motors.check_PMT_curvature_and_move()
        self.threshold = factor*self.measure_intensity()[0]

    def measure_profile(self, angle):
        #start far away from PMT taking into account beam diameter
        current_R = self.cfg.profile_r_start
        self.motors.check_PMT_curvature_and_move_polar(current_R, angle)

        intensity = self.measure_intensity()[0]
        if intensity>self.threshold:
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
            intensity = self.measure_intensity()
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
            self.motors.check_PMT_curvature_and_move_polar(current_R, angle)
                
        return(np.array(intensities), np.array(intensities_e), np.array(position), np.array(position_R))

    def interpolate_profile_intensity_point(self, centre,angle, R, charge, intensity):
        interpol = interp1d(charge,R)
        r_fifty = interpol(rand)
        xy_fifty = pol2cart(r_fifty, np.deg2rad(angle))
        return (centre[1]+xy_fifty[0],centre[2]+xy_fifty[1])

    def run(self):
        
        allangles = np.arange(0,360, self.cfg.number_profiles)
        x_data = np.array([])
        y_data = np.array([])
        timer = LoopTimer() 
        for angle in allangles:
            try:
                intensities, errors, positions, Rs = self.measure_profile(angle)
            except:
                continue
            try:
                newpoint = self.interpolate_profile_intensity_point(angle, Rs, intensities, intensity = norm[0]/3.)
                x_data = np.append(x_data,newpoint[1])
                y_data = np.append(y_data,newpoint[0])
            except Exception as err:
                log.error(f"{err}")

            timer.print_time_left()

            if large:
                np.save(anglefolder+"/lu_angle_"+str(int(angle)), (data,norm))
            else:
                np.save(anglefolder+"/QE_angle_"+str(int(angle)), (data,norm))
        
        if large:
            out = getcenter(allangles,np.linspace(100,250,50))
            print(out)
            f = open(anglefolder+"/lu_angle_deviation.txt","w")
            
        else:
            out = getcenter(allangles,np.linspace(norm[0]*0.3,norm[0]*0.7,50))
            print(out)
            f = open(anglefolder+"/QE_angle_deviation.txt","w")
        f.write("#x0, y0, R, stdx0, stdy0, minx0, maxx0, miny0,maxy0 \n")
        for i in out:
            f.write(str(i)+"\t")
        f.write("\n")
        f.close()