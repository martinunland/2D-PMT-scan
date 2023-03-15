from typing import Protocol, Tuple
import asyncio
import numpy as np


class DAQ_Device(Protocol):
    def connect():
        ...

    def disconnect():
        ...

    def read():
        ...


class TestOsci:
    def connect() -> None:
        print("Connecting oscilloscope")

    def disconnect() -> None:
        print("Disconnecting oscilloscope")

    async def read() -> Tuple[float, float]:
        await asyncio.sleep(2)
        return np.random.rand((10000, 200))

class TestPicoamp:
    def connect() -> None:
        print("Connecting picoamperemeter")

    def disconnect() -> None:
        print("Disconnecting picoamperemeter")

    async def read() -> Tuple[float, float]:
        await asyncio.sleep(2)
        return np.random.rand((10000, 200))