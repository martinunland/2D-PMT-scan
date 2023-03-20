from typing import TextIO
from .DAQ import DAQDevice
from .grids import Grid
from .data_analysis import DataAnalysis, PulseModeAnalysis
import asyncio
import logging
from .motor_grid_control import MotorsControl
from copy import deepcopy
from .config import Statistics
from .helper import get_hydrawd

log = logging.getLogger(__name__)


class ScanManager:
    def __init__(
        self,
        grid: Grid,
        motors: MotorsControl,
        device: DAQDevice,
        analyser: DataAnalysis,
        cfg: Statistics
    ) -> None:
        self.device = device
        self.analyser = analyser
        self.motors = motors
        self.grid = deepcopy(grid)
        self.readouts_per_position = cfg.readouts_per_position
        self.reference_period = cfg.reference_period

        self.measurements_since_last_reference = 0
        self.log_file = get_hydrawd().joinpath("positions_and_timestamps.txt")

    async def setup_analyser(self):
        if isinstance(self.analyser, PulseModeAnalysis):
            await self._make_time_axis_and_masks()

    async def _make_time_axis_and_masks(self) -> None:
        block, _ = await self.device.read()
        self.analyser.update_time_axis(block[0])

    async def read_and_append(self) -> None:
        block, timestamp = await self.device.read()
        self.run_timestamps.append(timestamp)
        self.analyser.append_data(block)

    async def measure_reference_device(self) -> None:
        log.info("Measuring reference device...")

        try:
            await asyncio.gather(
                self.motors.move_to_reference(), self.device.configure_for_secondary()
            )
            block, time_stamp = await self.device.read_reference()
            await asyncio.gather(
                self.analyser.analyse_reference(block, time_stamp),
                self.device.configure_for_primary(),
            )

        except Exception as e:
            log.error("Reference measurement failed with exception: " + str(e))

    async def move_to_next_grid_position(self) -> None:
        try:
            x, y = self.grid.valid_grid_positions.pop(0)
            if not await self.motors.check_PMT_curvature_and_move(x, y):
                await self.move_to_next_grid_position()
        except IndexError:
            log.info("No more points to scan...Finished!")

    async def check_if_reference_and_move(self) -> None:
        if self.measurements_since_last_reference > self.reference_period:
            await self.measure_reference_device()
            self.measurements_since_last_reference = 0
        await self.move_to_next_grid_position()

    async def read_analyse_and_move_async(self) -> None:
        log.info("Measuring current position")
        job_list = []
        self.run_timestamps = []
        job_list = [self.read_and_append for _ in range(self.readouts_per_position)]
        job_list.append(self.check_if_reference_and_move)

        for job in job_list:
            await asyncio.gather(job(), self.analyser.process_next())

    def log_motor_position(self, f: TextIO):
        log.debug("Saving set and read motor positions..")
        coordinates = self.motors.last_set_coordinates
        real_position = self.motors.get_current_position()
        coordinates.extend(real_position)
        for val in coordinates:
            f.write(str(val) + "\t")

    def log_timestamps(self, f: TextIO):
        log.debug("Saving timestamps to file...")
        for val in self.run_timestamps:
            f.write(str(val) + "\t")

    async def measure_log_info_and_move(self):
        with open(self.log_file, "a") as f:
            self.log_motor_position(f)
            await self.read_analyse_and_move_async()
            self.measurements_since_last_reference += 1
            self.log_timestamps(f)
            f.write("\n")

    async def run(self):
        await self.setup_analyser()
        await self.measure_reference_device()
        await self.move_to_next_grid_position()
        while len(self.grid.valid_grid_positions) > 0:
            await self.measure_log_info_and_move()
        await self.measure_reference_device()
