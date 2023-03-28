import logging
from typing import Protocol, Tuple
import asyncio
import numpy as np
from picoamp_control import PicoampControl
from .config import PicoscopeConfig, PicoamperemeterConfig
import time
from picoscope import picobase, ps6000

log = logging.getLogger(__name__)

class DAQDevice(Protocol):
    async def connect():
        ...

    async def disconnect():
        ...

    async def read():
        ...



class PicoampWrapper:
    def __init__(self, cfg: PicoamperemeterConfig) -> None:
        self.pico = PicoampControl()
        self.cfg = cfg

    def check_channel_configuration(self):
        assert self.cfg.primary_channel in [0,1], "PMT channel can be only 0 or 1"
        assert self.cfg.reference_channel in [0,1], "Reference channel can be only 0 or 1"
        assert self.cfg.primary_channel != self.cfg.reference_channel, "PMT and reference channels have to be different" 

    async def connect(self) -> None:
        log.info("Connecting picoamperemeter async...")
        await self.pico.connect()
        await self.pico.auto_config()

    async def disconnect(self) -> None:
        log.info("Disconnecting picoamperemeter async...")
        await self.pico.close_instrument()

    async def read(self) -> Tuple[float, float]:
        return await self.pico.get_mean_current(self.cfg.count_per_read)

    async def read_reference(self) -> Tuple[float, float]:
        return await self.pico.get_mean_current(self.cfg.count_per_read)




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

    async def read(self):
        log.debug("Reading picoamp...")
        await asyncio.sleep(2)
        relerror = 0.01
        mean = 52
        PMT = (np.random.normal(mean, relerror*mean, 1)[0], np.random.normal(relerror*mean, relerror*mean, 1)[0])
        diode = (np.random.normal(mean, relerror*mean, 1)[0], np.random.normal(relerror*mean, relerror*mean, 1)[0])
        return (PMT,diode), time.time()

    async def read_reference(self):
        log.debug("Reading picoamp reference...")
        await asyncio.sleep(2)
        relerror = 0.01
        mean = 52
        PMT = (np.random.normal(mean, relerror*mean, 1)[0], np.random.normal(relerror*mean, relerror*mean, 1)[0])
        diode = (np.random.normal(mean, relerror*mean, 1)[0], np.random.normal(relerror*mean, relerror*mean, 1)[0])
        return (PMT,diode), time.time()

    async def configure_for_primary(self):
        pass
    async def configure_for_secondary(self):
        pass