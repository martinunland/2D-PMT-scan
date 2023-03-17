import asyncio
import pathlib
from typing import List, Tuple
import numpy as np
import logging
from typing import Protocol
from scipy.integrate import simps
from .config import Picoscope_config, Picoamperemeter_config
from .helper import make_folder_in_hydrawd

log = logging.getLogger(__name__)


class Data_Analysis(Protocol):
    def append_data(data: np.ndarray) -> None:
        ...

    def analyse_reference(data: np.ndarray, timestamp: float) -> None:
        ...

    async def process_next() -> None:
        ...


class Pulse_Mode_Analysis:
    def __init__(self, cfg_picoscope: Picoscope_config) -> None:
        self.data_to_analyse = []
        self.cfg = cfg_picoscope
        self.current_position_index = 0
        self._make_folder_and_data_file()

    def _make_folder_and_data_file(self):
        path = make_folder_in_hydrawd("data_pulse_mode/")
        self.reference_file_name = path.joinpath("second_PMT_reference.txt")
        self.data_file_name_prefix = path.joinpath("pulse_mode_scan")

    def update_time_axis(self, waveform):
        log.debug("Updating/making time axis and baseline/signal masks...")
        self.time_axis = np.arange(0, waveform.size, 1) * self.cfg.sampling_interval

        self.baseline_mask = np.logical_and(
            self.time_axis > self.cfg.baseline_tmin,
            self.time_axis < self.cfg.baseline_tmax,
        )
        self.ref_baseline_mask = np.logical_and(
            self.time_axis > self.cfg.reference_baseline_tmin,
            self.time_axis < self.cfg.reference_baseline_tmax,
        )
        self.ref_signal_mask = np.logical_and(
            self.time_axis > self.cfg.reference_signal_tmin,
            self.time_axis < self.cfg.reference_signal_tmax,
        )
        log.debug("Finished making time axis & masks!")

    def append_data(self, data):
        log.spam("Appended data of shape %s", data.shape)
        self.data_to_analyse.append(data)
        log.spam("Current data_to_analyse length %s", len(self.data_to_analyse))

    def get_pulse_shape(
        self, x: np.ndarray, y: np.ndarray
    ) -> Tuple[float, float, float]:
        log.spam("Calculating pulse shape parameters")
        if not isinstance(x, np.ndarray):
            raise TypeError("x must be a numpy array")
        if not isinstance(y, np.ndarray):
            raise TypeError("y must be a numpy array")

        max_index, max_val, x_at_max = self.get_max_index(x, y)
        first_part = x <= x_at_max
        second_part = x >= x_at_max

        x1_ar, x2_ar = [], []
        limits = np.array([0.8, 0.5, 0.2])
        for limit in limits:
            for idx, val in enumerate(y[first_part][::-1]):
                if val < limit * max_val:
                    x1_ar.append(
                        np.interp(
                            limit * max_val,
                            [val, y[first_part][::-1][idx - 1]],
                            [x[first_part][::-1][idx], x[first_part][::-1][idx - 1]],
                        )
                    )
                    break
            for idx, val in enumerate(y[second_part]):
                if val < limit * max_val:
                    x2_ar.append(
                        np.interp(
                            limit * max_val,
                            [y[second_part][idx - 1], val],
                            [x[second_part][::-1][idx - 1], x[second_part][::-1][idx]],
                        )
                    )
                    break

        FWHM = x2_ar[1] - x1_ar[1]
        RT = x1_ar[0] - x1_ar[2]
        FT = x2_ar[2] - x2_ar[0]

        return FWHM, RT, FT

    def get_baseline(
        self, waveformBlock: np.ndarray, mask: np.ndarray
    ) -> Tuple[float, float]:
        log.spam("Calculating mean baseline level of data block...")
        baselines = []
        for waveform in waveformBlock:
            baselines.append(waveform[mask])
        return np.average(baselines), np.std(baselines) / np.sqrt(len(baselines) - 1)

    def get_max_index(self, x, y):
        log.spam("Getting index max")
        max_index = np.argmax(y)
        max_val = y[max_index]
        x_at_max = x[max_index]
        return max_index, max_val, x_at_max

    def extract_pulse_region(self, waveform, max_index):
        log.spam("Selecting region of interest")
        start_index = max_index - int(15e-9 / self.cfg.sampling_interval)
        end_index = max_index + int(15e-9 / self.cfg.sampling_interval)
        start_index = max(start_index, 0)
        end_index = min(end_index, len(waveform) - 1)
        pulse = waveform[start_index:end_index]
        pulse_time = self.time_axis[start_index:end_index]
        return pulse, pulse_time

    def process_waveform(self, waveform) -> List:
        log.spam("Processing waveform")
        max_index, amplitude, transit_time = self.get_max_index(
            self.time_axis, waveform
        )
        pulse, pulse_time = self.extract_pulse_region(waveform, max_index)

        try:
            FWHM, RT, FT = self.get_pulse_shape(pulse_time, pulse)
        except Exception as err:
            FWHM, RT, FT = [-1, -1, -1]
            log.spam(
                "Calculating pulse shape parameters failed, passing default values"
            )

        log.spam("Calculating charges")
        charge = simps(pulse * 1e-3, pulse_time * 1e-9)
        pedestal_charge = simps(
            waveform[self.baseline_mask] * 1e-3,
            self.time_axis[self.baseline_mask] * 1e-9,
        )
        log.spam("Finished processing waveform")
        return pedestal_charge, transit_time, charge, amplitude, FWHM, RT, FT

    async def process_data(self, waveform_block: np.ndarray) -> None:
        log.spam("Proccesing data block...")
        baseline, baseline_error = self.get_baseline(waveform_block, self.baseline_mask)
        with open(
            self.data_file_name_prefix.with_name(f"{self.current_position_index}.txt"), "a"
        ) as f:
            for waveform in waveform_block:
                values = self.process_waveform(waveform - baseline)
                for value in values:
                    f.write(str(value) + "\t")
                f.write("\n")
        log.spam("Finished processing data block...")

    async def process_next(self) -> None:
        try:
            log.debug("Processing data chunk...")
            waveform_block = self.data_to_analyse.pop(0)
            await self.process_data(waveform_block)
            self.current_position_index += 1
        except IndexError as err:
            log.spam("Data list empty, nothing to analyse")

    async def analyse_reference(self, data: np.ndarray, timestamp: float) -> None:
        baseline, baseline_error = self.get_baseline(data, self.ref_baseline_mask)
        charge = []
        for waveform in data:
            charge.append(
                simps(
                    waveform[self.ref_signal_mask] - baseline,
                    self.time_axis[self.ref_signal_mask],
                )
            )
        mean = np.mean(charge)
        error = np.std(charge) / np.sqrt(len(charge) - 1)

        with open(self.reference_file_name, "a") as f:
            for val in [timestamp, mean, error]:
                f.write(str(val) + "\t")
            f.write("\n")


class Current_Mode_Analysis:
    def __init__(self, cfg: Picoamperemeter_config) -> None:
        self.cfg = cfg
        self.data_to_write = []
        self.lines_written = 0
        self._make_folder_and_data_file()

    def _make_folder_and_data_file(self):
        path = make_folder_in_hydrawd("data_current_mode/")
        self.reference_file_name = path.joinpath("photodiode_reference.txt")
        self.data_file_name = path.joinpath("photocurrent_scan.txt")

    def append_data(self, data: np.ndarray) -> None:
        self.data_to_write.append(data)

    async def analyse_reference(self, data: np.ndarray) -> None:
        await self.write_data(data, self.reference_file_name)

    def write_header(self, file_name):
        with open(file_name, "a") as f:
            f.write("#")
            for i in range(2):
                for value in ["Mean_chn." + str(i), "Standard_error_chn." + str(i)]:
                    f.write(value + "\t")
            f.write("\n")

    def write_data(self, data, file_name):
        if self.lines_written == 0:
            self.write_header(file_name)
        with open(file_name, "a") as f:
            for value in data:
                f.write(str(value) + "\t")
            f.write("\n")
            self.lines_written += 1

    async def process_next(self) -> None:
        try:
            data = self.data_to_write.pop(0)
            await self.write_data(data, self.data_file_name)
        except IndexError:
            logging.debug("No data to analyse")
            pass
