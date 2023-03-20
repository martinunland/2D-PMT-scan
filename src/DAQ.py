import logging
from typing import Protocol, Tuple
import asyncio
import numpy as np
import time
log = logging.getLogger(__name__)

class DAQDevice(Protocol):
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
        def gaussian(x,a,b,c):
            return a*np.exp(-(x-b)**2/np.sqrt(2*c**2))
        log.debug("Reading picoscope...")
        await asyncio.sleep(2)
        x = np.linspace(0,200,200)
        amps = np.reshape(np.random.normal(7,2, 10000), (10000,1))
        gaussians = np.reshape(gaussian(x, 1, 100, 5), (1,200))
        waveforms = np.random.rand(10000, 200)+amps*gaussians
        return waveforms, time.time()

    async def read_reference(self)-> Tuple[np.ndarray, float]:
        def gaussian(x,a,b,c):
            return a*np.exp(-(x-b)**2/np.sqrt(2*c**2))
        await asyncio.sleep(2)
        x = np.linspace(0,200,200)
        amps = np.reshape(np.random.normal(20,2, 10000), (10000,1))
        gaussians = np.reshape(gaussian(x, 1, 100, 5), (1,200))
        waveforms = np.random.rand(10000, 200)+amps*gaussians
        return waveforms, time.time()
        
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