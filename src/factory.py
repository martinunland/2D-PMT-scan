from src.DAQ import TestOsci, TestPicoamp
from src.data_analysis import PulseModeAnalysis, CurrentModeAnalysis
from src.motor_grid_control import MotorsControl
from helper import MeasurementMode


class DeviceFactory:
    @staticmethod
    def create_analyser_and_daq(mode: MeasurementMode, motors: MotorsControl, cfg: object):
        if mode == MeasurementMode.PULSE:
            return DeviceFactory._create_pulse_mode_analyser_and_daq(motors, cfg)
        elif mode == MeasurementMode.CURRENT:
            return DeviceFactory._create_current_mode_analyser_and_daq(motors, cfg)
        else:
            raise ValueError(f"Unsupported mode: {mode}")

    @staticmethod
    def _create_pulse_mode_analyser_and_daq(motors: MotorsControl, cfg: object):
        motors.set_default_reference_callable(motors.move_to_second_PMT)
        analyzer = PulseModeAnalysis(cfg.picoscope)
        daq = TestOsci()
        return analyzer, daq

    @staticmethod
    def _create_current_mode_analyser_and_daq(motors: MotorsControl, cfg: object):
        motors.set_default_reference_callable(motors.move_to_diode)
        analyzer = CurrentModeAnalysis(cfg.picoamp)
        daq = TestPicoamp()
        return analyzer, daq
