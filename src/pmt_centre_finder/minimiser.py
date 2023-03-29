from dataclasses import dataclass
import logging
import pathlib
from typing import Tuple
from alive_progress import alive_bar
from iminuit import Minuit
import numpy as np
from scipy.interpolate import interp1d
from src.motor_grid_control import pol2cart


log = logging.getLogger(__name__)


@dataclass
class ProfileData:
    measured_intensity: np.ndarray
    intensity_error: np.ndarray
    position: np.ndarray
    R: np.ndarray
    centre_intensity: np.ndarray
    threshold: np.ndarray


class PMT_circle_fitting:
    def __init__(
        self,
        PMT_radius: float,
        centre: list,
        data_folder: pathlib.Path,
        profile_angles: np.ndarray,
    ):
        self.R_p0 = PMT_radius
        self.centre = centre
        self.data_folder = data_folder
        self.profile_angles = profile_angles
        self.NR_FITS = 20
        self.MEAN_INTENSITY_COUNTS_PER_FIT = 10
        self._get_data_from_files()
        self._calculate_intensities_to_fit()

    def _calculate_intensities_to_fit(self):
        centre_intensity = []
        threshold = []
        for _, item in self.data.items():
            centre_intensity.append(item.centre_intensity[0])
            threshold.append(item.threshold)
        centre_intensity = np.mean(centre_intensity)
        threshold = np.mean(threshold)
        self.MIN_INTENSITY = threshold
        self.MAX_INTENSITY = centre_intensity / 2.0
        log.debug(f"Intensities used in fits range from {self.MIN_INTENSITY:.3g} to {self.MAX_INTENSITY:.3g}")

    def _get_data_from_files(self):
        self.data = {}
        for angle in self.profile_angles:
            try:
                self.data[angle] = ProfileData(
                    *np.load(
                        self.data_folder / f"profile_{angle}deg.npy",
                        allow_pickle=1,
                    )
                )
            except Exception as err:
                log.error(err)
                pass
        assert (
            len(self.data) > 3
        ), f"Something went wrong, number of profiles measured ({len(self.data)}) too low (you need at least 4)!"

    def interpolate_profile_intensity_point(self, angle, R, charge, intensity):
        interpol = interp1d(charge, R)
        interp_R = interpol(intensity)
        interp_x_y = pol2cart(interp_R, np.deg2rad(angle))
        return (self.centre[1] + interp_x_y[0], self.centre[2] + interp_x_y[1])

    def fit_profiles_and_get_PMT_centre(
        self,
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        log.info("Fitting profile data several times to avoid systematics...")

        all_ints = np.linspace(self.MIN_INTENSITY, self.MAX_INTENSITY, 1000)
        x0_fits = []
        y0_fits = []
        with alive_bar(self.NR_FITS, enrich_print = False, title="Fitting profiles") as bar:
            for _ in range(self.NR_FITS):
                n = max(2, np.random.poisson(self.MEAN_INTENSITY_COUNTS_PER_FIT))
                x_0, y_0 = self.get_centre_from_intensity_set(
                    intensity_levels=np.random.choice(all_ints, n)
                )
                x0_fits.append(x_0)
                y0_fits.append(y_0)
        mean_x0 = np.mean(x0_fits)
        mean_y0 = np.mean(y0_fits)
        error_x0 = np.std(x0_fits)
        error_y0 = np.std(y0_fits)
        log.info(
            f"PMT centre is at: x={mean_x0:.2f}+-{error_x0:.2f}, x={mean_y0:.2f}+-{error_y0:.2f}"
        )

        return (mean_x0, error_x0), (mean_y0, error_y0)

    def get_centre_from_intensity_set(self, intensity_levels) -> Tuple[float, float]:

        self.datasets = []
        for _ in intensity_levels:
            self.datasets.append([[], []])

        for angle, profile_data in self.data.items():
            for i, interp_intensity in enumerate(intensity_levels):
                try:
                    interp_cartesian = self.interpolate_profile_intensity_point(
                        angle,
                        profile_data.R,
                        profile_data.measured_intensity,
                        interp_intensity,
                    )
                    self.datasets[i][0].append(interp_cartesian[1])
                    self.datasets[i][1].append(interp_cartesian[0])
                except Exception as err:
                    print(err)
                    pass
        for i, _ in enumerate(intensity_levels):
            self.datasets[i][0] = np.array(self.datasets[i][0])
            self.datasets[i][1] = np.array(self.datasets[i][1])

        self.minimize()
        fit_parameters = self.m.np_values()
        return fit_parameters[-2], fit_parameters[-1]

    def log_likelihood(self, *args):

        xc = args[-2]
        yc = args[-1]
        Rs = args[:-2]
        totallh = 0
        for i, R in enumerate(Rs):
            x = self.datasets[i][0]
            y = self.datasets[i][1]
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
        for i in range(len(self.datasets)):
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
