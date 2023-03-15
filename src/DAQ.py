import logging
from typing import Protocol, Tuple
import asyncio
import numpy as np
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

    async def read(self) -> Tuple[float, float]:
        await asyncio.sleep(2)
        return np.random.rand((10000, 200))

class TestPicoamp:
    async def connect(self) -> None:
        log.info("Connecting picoamperemeter...")
        await asyncio.sleep(2)

    async def disconnect(self) -> None:
        log.info("Disconnecting picoamperemeter...")
        await asyncio.sleep(2)

    async def read(self) -> Tuple[float, float]:
        await asyncio.sleep(2)
        return np.random.rand((10000, 200))