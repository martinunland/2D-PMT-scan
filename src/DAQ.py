import logging
from typing import Protocol, Tuple
import asyncio
import numpy as np
import time
log = logging.getLogger(__name__)

class DAQ_Device(Protocol):
    async def connect():
        ...

    async def disconnect():
        ...

    async def read():
        ...


class TestOsci:
    async def connect(self) -> None:
        log.info("Connecting picoscope...")
        await asyncio.sleep(2)

    async def disconnect(self) -> None:
        log.info("Disconnecting picoscope...")
        await asyncio.sleep(2)

    async def read(self) -> Tuple[np.ndarray, float]:
        await asyncio.sleep(2)
        return np.random.rand(200, 10000), time.time()

    async def read_reference(self)-> Tuple[np.ndarray, float]:
        await asyncio.sleep(2)
        return np.random.rand(200, 10000), time.time()
        
    async def configure_for_primary(self):
        log.debug("Configuring picoscope for scan measurement...")
        await asyncio.sleep(0.2)
        pass

    async def configure_for_secondary(self):
        log.debug("Configuring picoscope for reference measurement...")
        await asyncio.sleep(0.2)
        pass

class TestPicoamp:
    async def connect(self) -> None:
        log.info("Connecting picoamperemeter...")
        await asyncio.sleep(2)

    async def disconnect(self) -> None:
        log.info("Disconnecting picoamperemeter...")
        await asyncio.sleep(2)

    async def read(self) -> Tuple[np.ndarray, float]:
        await asyncio.sleep(2)
        return np.random.rand(1000), time.time()