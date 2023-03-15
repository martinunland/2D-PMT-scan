from typing import TextIO
from .DAQ import DAQ_Device
from .grids import Grid
from .data_analysis import Data_Analysis
import asyncio
import logging
from .motor_grid_control import Motors_Control
from copy import deepcopy


log = logging.getLogger(__name__)


class Scan_Manager:
    def __init__(
        self,
        grid: Grid,
        motors: Motors_Control,
        device: DAQ_Device,
        analyser: Data_Analysis,
    ) -> None:
        self.device = device
        self.analyser = analyser
        self.motors = motors
        self.grid = deepcopy(grid)
        self.readouts_per_position = 5
        self.counts_since_last_reference = 0
        self.reference_period = 30
        self.log_file = "positions_and_timestamps.txt"

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
            block = await self.device.read(channel=self.device.secondary_channel)
            await self.device.configure_for_primary()
            await self.analyser.analyse_reference(block)

        except Exception as e:
            log.error("Reference measurement failed with exception: " + str(e))

    async def move_to_next_grid_position(self) -> None:
        try:
            x, y = self.grid.valid_grid_positions.pop(0)
            if not await self.motors.check_PMT_curvature_and_move(x, y):
                self.move_to_next_grid_position()
        except IndexError:
            log.info("No more points to scan...Finished!")

    async def check_if_reference_and_move(self) -> None:
        if self.counts_since_last_reference > self.reference_period:
            await self.measure_reference_device()
            self.counts_since_last_reference = 0
        await self.move_to_next_grid_position()

    async def measure_current_position(self) -> None:
        log.debug("Measuring current position")
        job_list = []
        self.run_timestamps = []
        job_list = [self.read_and_append for _ in range(self.readouts_per_position)]
        job_list.append(self.check_if_reference_and_move)

        for job in job_list:
            await asyncio.gather(job(), self.analyser.process_next())

    async def log_position_info(self, f: TextIO):
        log.debug("Saving set and read motor positions..")
        set_coordinate = self.motors.last_set_coordinates
        real_position = self.motors.get_current_position()
        for val in set_coordinate.extend(real_position):
            f.write(str(val) + "\t")

    async def log_timestamps(self, f: TextIO):
        log.debug("Saving timestamps to file...")
        for val in self.run_timestamps:
            f.write(str(val) + "\t")

    async def single_run(self):
        with open(self.log_file, "a") as f:
            self.log_position_info(f)
            await self.measure_current_position()
            self.counts_since_last_reference += 1
            self.log_timestamps(f)
            f.write("\n")

    async def run(self):
        await self.measure_reference_device()
        await self.move_to_next_grid_position()
        while len(self.grid.valid_grid_positions) > 0:
            await self.single_run()
            await self.move_to_next_grid_position()
        await self.measure_reference_device()
