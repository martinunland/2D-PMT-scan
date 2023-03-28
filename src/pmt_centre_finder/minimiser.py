from dataclasses import dataclass
import logging
import pathlib
from typing import Tuple
from iminuit import Minuit
import numpy as np
from scipy.interpolate import interp1d
from motor_grid_control import pol2cart

log = logging.getLogger(__name__)

@dataclass
class ProfileData:
    measured_intensity: np.ndarray
    intensity_error: np.ndarray
    position: np.ndarray
    R: np.ndarray
    centre_intensity: np.ndarray


class PMT_circle_fitting:
    def __init__(
        self, centre: list, data_folder: pathlib.Path, profile_angles: np.ndarray
    ):
        self.centre = centre
        self.data_folder = data_folder
        self.profile_angles = profile_angles
        self.NR_FITS = 20
        self.MEAN_INTENSITY_COUNTS_PER_FIT = 10
        self.get_data_from_files()

    def get_data_from_files(self):
        self.data = {}
        for angle in self.profile_angles:
            try:
                self.data[angle] = ProfileData(
                    *np.load(
                        self.data_folder.join(f"profile_{angle}deg.npy"), allow_pickle=1
                    )
                )
            except:
                pass
        assert (
            len(self.data) > 3
        ), f"Something went wrong, number of profiles measured ({len(self.data)}) too low (you need at least 4)!"

    def interpolate_profile_intensity_point(self, angle, R, charge, intensity):
        interpol = interp1d(charge, R)
        interp_R = interpol(intensity)
        interp_x_y = pol2cart(interp_R, np.deg2rad(angle))
        return (self.centre[1] + interp_x_y[0], self.centre[2] + interp_x_y[1])

    def get_centre_with_error(self):
        log.info("Fitting profile data several times to avoid systematics...")

        all_ints = np.linspace(self.MIN_INTENSITY, self.MAX_INTENSITY, 1000)
        x0_fits = []
        y0_fits = []
        for i in range(self.NR_FITS):
            n = max(2,np.random.poisson(self.MEAN_INTENSITY_COUNTS_PER_FIT))
            x_0,y_0=self.get_centre_from_intensity_set(intensity_levels=np.random.choice(all_ints, n))
            x0_fits.append(x_0)
            y0_fits.append(y_0)
        mean_x0 = np.mean(x0_fits)
        mean_y0 = np.mean(y0_fits)
        error_x0 = np.std(x0_fits)
        error_y0 = np.std(y0_fits)
        return (mean_x0, error_x0), (mean_y0, error_y0)

    def get_centre_from_intensity_set(self, intensity_levels)->Tuple[float, float]:

        datasets = []
        for _ in intensity_levels:
            datasets.append([[], []])

        for angle, profile_data in self.data.items():
            for i, interp_intensity in enumerate(intensity_levels):
                try:
                    interp_cartesian = self.interpolate_profile_intensity_point(
                        angle, profile_data.R, profile_data.measured_intensity, interp_intensity
                    )
                    datasets[i][0].append(interp_cartesian[1])
                    datasets[i][1].append(interp_cartesian[0])
                except Exception as err:
                    print(err)
                    pass
        for i, _ in enumerate(intensity_levels):
            datasets[i][0] = np.array(datasets[i][0])
            datasets[i][1] = np.array(datasets[i][1])

        self.minimize()
        fit_parameters = self.m.np_values()
        return fit_parameters[-2], fit_parameters[-1]

    def log_likelihood(self, *args):

        xc = args[-2]
        yc = args[-1]
        Rs = args[:-2]
        totallh = 0
        for i, R in enumerate(Rs):
            x = self.dataset[i][0]
            y = self.dataset[i][1]
            model = np.sqrt((x - xc) ** 2.0 + (y - yc) ** 2.0) - R
            totallh += -0.5 * np.sum((model) ** 2)
        return -totallh

    def minimize(self):
        self.create_iminuit()
        self.m = Minuit(self.log_likelihood, name=self.parname, **self.minuit_args)
        self.m.migrad()
        self.m.hesse()

    def create_iminuit(self):
        initial = {}
        limits = {}
        fix = {}
        error = {}
        parname = list()
        for i in range(len(self.dataset)):
            parname.append("R_" + str(i))
            initial[parname[-1]] = self.R_p0
            limits["limit_" + parname[-1]] = (self.R_p0 - 5, self.R_p0 + 5)
            limits["error_" + parname[-1]] = 10.0
            fix["fix_" + parname[-1]] = False
        for i, par in enumerate(["X0", "Y0"]):
            parname.append(par)
            initial[parname[-1]] = 100
            limits["limit_" + parname[-1]] = (0, None)
            limits["error_" + parname[-1]] = 10.0
            fix["fix_" + parname[-1]] = False

        self.minuit_args = {**initial, **limits, **error, **fix, **dict(errordef=0.5)}
        self.parname = parname
