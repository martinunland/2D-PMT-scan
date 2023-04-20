import asyncio
import os
import pathlib
from typing import List, Tuple
import numpy as np
import logging
from typing import Protocol
from scipy.integrate import simps
from .config import PicoscopeConfig, PicoamperemeterConfig
from .helper import make_folder_in_working_directory
from pulse_mode_analysis import PulseModeAnalysis

log = logging.getLogger(__name__)


class DataAnalysis(Protocol):
    """
    Protocol class for data analysis implementations.

    Provides a general structure for data analysis of different modes.
    """

    async def process_next(self) -> None:
        """
        Process the next data block in the queue.
        """
        ...

    async def append_data(self, data):
        """
        Append new data to the data queue.

        Args:
            data: The data to be appended to the queue.
        """
        ...

    async def analyse_reference(self, block, time_stamp: float) -> None:
        """
        Analyse the reference data block.

        Args:
            block: The reference data block to be analyzed.
            time_stamp: The timestamp of the reference data block.
        """
        ...


class PulseModeAnalysisWrapper:
    """
    Data analysis implementation for pulse mode measurements.
    """

    def __init__(self, cfg_picoscope: PicoscopeConfig) -> None:
        self.data_to_analyse = []
        self.cfg = cfg_picoscope
        self.current_position_index = 0
        self._make_folder_and_data_file()
        self.PMT_analyser = PulseModeAnalysis(
            self.cfg.sampling_interval, self.cfg.baseline_tmin, self.cfg.baseline_tmax
        )
        self.reference_analyser = PulseModeAnalysis(
            self.cfg.sampling_interval,
            self.cfg.reference_baseline_tmin,
            self.cfg.reference_baseline_tmax,
        )

    def _make_folder_and_data_file(self):
        path = make_folder_in_working_directory("data_pulse_mode/")
        self.reference_file_name = path.joinpath("second_PMT_reference.txt")
        self.data_file_name_prefix = path.joinpath("pulse_mode_scan")

    def update_time_axis(self, waveform):
        """
        Make the time array based on the configured waveform length.

        Args:
            block: The input data block containing the waveforms.
        """
        log.debug("Updating/making time axis and baseline/signal masks...")

        self.PMT_analyser.baseline_tmin = self.cfg.baseline_tmin
        self.PMT_analyser.baseline_tmax = self.cfg.baseline_tmax

        self.reference_analyser.baseline_tmin = self.cfg.reference_baseline_tmin
        self.reference_analyser.baseline_tmax = self.cfg.reference_baseline_tmax

        self.PMT_analyser.update_time_axis(waveform)
        self.reference_analyser.update_time_axis(waveform)

        self.ref_signal_mask = np.logical_and(
            self.reference_analyser.time_axis > self.cfg.reference_signal_tmin,
            self.reference_analyser.time_axis < self.cfg.reference_signal_tmax,
        )
        log.debug("Finished making time axis & masks!")

    def append_data(self, data):
        """
        Append new data to the data queue.

        Args:
            data: The data to be appended to the queue.
        """
        log.debug("Appended data of shape %s", data.shape)
        self.data_to_analyse.append(data)
        log.debug("Current data_to_analyse length %s", len(self.data_to_analyse))

    async def process_data(self, waveform_block: np.ndarray) -> None:
        log.debug("Proccesing data block...")
        baseline, _ = self.PMT_analyser.get_baseline(waveform_block)
        with open(
            self.data_file_name_prefix.with_name(f"{self.current_position_index}.txt"),
            "a",
        ) as f:
            for waveform in waveform_block:
                values = self.PMT_analyser.process_waveform(waveform - baseline)
                for value in values:
                    f.write(str(value) + "\t")
                f.write("\n")
        log.debug("Finished processing data block...")

    async def process_next(self) -> None:
        """
        Process the next data block in the queue.
        """
        try:
            log.debug("Processing data chunk...")
            waveform_block = self.data_to_analyse.pop(0)
            await self.process_data(waveform_block)
            self.current_position_index += 1
        except IndexError as err:
            log.debug("Data list empty, nothing to analyse")

    async def analyse_reference(self, data: np.ndarray, timestamp: float) -> None:
        """
        Analyse the data taken from reference device.

        Args:
            block: The reference data block to be analyzed.
            time_stamp: The timestamp of the reference data block.
        """
        (mean, error), _ = self.reference_analyser.get_simple_intensity(
            data, self.ref_signal_mask
        )

        with open(self.reference_file_name, "a") as f:
            for val in [timestamp, mean, error]:
                f.write(str(val) + "\t")
            f.write("\n")


class CurrentModeAnalysis:
    """
    Data analysis implementation for current mode measurements.
    """

    def __init__(self, cfg: PicoamperemeterConfig) -> None:
        self.cfg = cfg
        self.data_to_write = []
        self._make_folder_and_data_file()

    def _make_folder_and_data_file(self):
        path = make_folder_in_working_directory("data_current_mode/")
        self.reference_file_name = path.joinpath("photodiode_reference.txt")
        self.data_file_name = path.joinpath("photocurrent_scan.txt")

    def get_simple_intensity(self, data):
        return data[self.cfg.primary_channel], data[self.cfg.reference_channel]

    def append_data(self, data) -> None:
        self.data_to_write.append(data)

    async def analyse_reference(self, data, timestamp) -> None:
        self.write_data(data, self.reference_file_name)

    def write_header(self, file_name):
        with open(file_name, "a") as f:
            f.write("#")
            for i in range(2):
                for value in ["Mean_chn." + str(i), "Standard_error_chn." + str(i)]:
                    f.write(value + "\t")
            f.write("Timestamp \n")

    def write_data(self, data, file_name: pathlib.Path):
        with open(file_name, "a") as f:
            if os.stat(file_name).st_size == 0:
                self.write_header(file_name)
            for tuple in data:
                for value in tuple:
                    f.write(str(value) + "\t")
            f.write("\n")

    async def process_next(self) -> None:
        try:
            data = self.data_to_write.pop(0)
            self.write_data(data, self.data_file_name)
        except IndexError:
            logging.debug("No data to analyse")
            pass
