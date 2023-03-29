"""
minimiser.py

This module contains the PMT_circle_fitting class, which is used to find the 
center of a Photomultiplier Tube (PMT) by analysing the intensity profiles 
measured at different angles.

Classes:
    - ProfileData: A dataclass that holds the measured data of a single profile.
    - PMT_circle_fitting: A class that uses the measured intensity profiles at various 
                          angles to fit circles and find the center of the PMT.
"""
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
    """
    A class that uses the measured intensity profiles at various angles to fit circles
    and find the centre of the PMT.

    Methods:
        - _calculate_intensities_to_fit: Calculates the range of intensities to be interpolated for the fits.
        - _load_data_from_files: Loads the profile data from the saved files.
        - interpolate_profile_intensity_point: Interpolates the intensity points for a given profile.
        - fit_profiles_and_get_PMT_centre: Performs multiple fits on the intensity profiles to find the centre of the PMT and calculates the uncertainties.
        - get_centre_from_intensity_set: Fits the centre of the PMT for a given set of intensity levels.
        - log_likelihood: Calculates the log-likelihood for the given model parameters.
        - minimise: Minimises the log-likelihood function using the iminuit package.
        - create_iminuit: Creates an iminuit object with the necessary initial parameters, limits, errors, and fixed status.
    """

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
        self._load_data_from_files()
        self._calculate_intensities_to_fit()

    def _calculate_intensities_to_fit(self) -> None:
        centre_intensity = []
        threshold = []
        for _, item in self.data.items():
            centre_intensity.append(item.centre_intensity[0])
            threshold.append(item.threshold)
        centre_intensity = np.mean(centre_intensity)
        threshold = np.mean(threshold)
        self.MIN_INTENSITY = threshold
        self.MAX_INTENSITY = centre_intensity / 2.0
        log.debug(
            f"Intensities used in fits range from {self.MIN_INTENSITY:.3g} to {self.MAX_INTENSITY:.3g}"
        )

    def _load_data_from_files(self) -> None:
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

    def interpolate_profile_intensity_point(
        self, angle: float, R: np.ndarray, charge: np.ndarray, intensity: float
    ) -> Tuple[float, float]:
        """
        Interpolate the Cartesian position of a point on the profile curve at a given intensity level.

        Args:
            angle (float): The angle of the profile curve in degrees.
            R (np.ndarray): The radial distance from the centre to the fibre position for each intensity value.
            charge (np.ndarray): The measured intensity values along the profile.
            intensity (float): The intensity level at which the position should be interpolated.

        Returns:
            Tuple[float, float]: The interpolated Cartesian coordinates (x, y) of the point on the profile curve at the given intensity level.
        """
        interpol = interp1d(charge, R)
        interp_R = interpol(intensity)
        interp_x_y = pol2cart(interp_R, np.deg2rad(angle))
        return (self.centre[1] + interp_x_y[0], self.centre[2] + interp_x_y[1])

    def fit_profiles_and_get_PMT_centre(
        self,
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Fit the circle profiles multiple times to find the PMT centre and estimate its uncertainty.

        Returns:
            Tuple[Tuple[float, float], Tuple[float, float]]: A tuple containing:
                - the x-coordinate of the PMT centre and its error,
                - the y-coordinate of the PMT centre and its error.
        """
        log.info("Fitting profile data several times to avoid systematics...")

        all_ints = np.linspace(self.MIN_INTENSITY, self.MAX_INTENSITY, 1000)
        x0_fits = []
        y0_fits = []
        with alive_bar(
            self.NR_FITS, enrich_print=False, title="Fitting profiles"
        ) as bar:
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

    def get_centre_from_intensity_set(self, intensity_levels:np.ndarray) -> Tuple[float, float]:
        """
        Fit the circle profiles for a given set of intensity levels and return the estimated PMT centre.

        Args:
            intensity_levels (np.ndarray): An array of intensity levels to use for fitting.

        Returns:
            Tuple[float, float]: The estimated x and y coordinates of the PMT centre.
        """
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
                    log.error(err)
                    pass
        for i, _ in enumerate(intensity_levels):
            self.datasets[i][0] = np.array(self.datasets[i][0])
            self.datasets[i][1] = np.array(self.datasets[i][1])

        self.minimise()
        fit_parameters = self.m.np_values()
        return fit_parameters[-2], fit_parameters[-1]

    def log_likelihood(self, *args)->float:
        """
        Calculate the log-likelihood of the model for the given parameters.

        Args:
            *args: The model parameters: the radii of the circles for each intensity level, followed by the x and y coordinates of the centre.

        Returns:
            float: The log-likelihood of the model.
        """
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

    def minimise(self)->None:
        """
        Perform the minimisation of the log-likelihood using the iminuit package.
        """
        self.create_iminuit()
        self.m = Minuit(self.log_likelihood, name=self.parname, **self.minuit_args)
        self.m.migrad()
        self.m.hesse()

    def create_iminuit(self)->None:
        """
        Create an iminuit Minuit object with initial parameters, limits, errors, and fixed parameter settings.
        """
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
