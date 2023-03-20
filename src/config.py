from dataclasses import dataclass

@dataclass
class CircularConstantDensity_config:
    r_max: float
    r_step: float

@dataclass
class Centre_find_config:
    number_profiles: int
    profile_r_start: float
    profile_r_stop: float
    coarse_step: float
    fine_step: float
    fit_results_file: str

@dataclass
class MotorConfig:
    COM_motors: list
    z_at_PMT_centre: float
    PMT_curvature_mapping: str

@dataclass
class PicoscopeConfig:
    primary_channel: str
    reference_channel: str
    sampling_interval: float
    baseline_tmin: float
    baseline_tmax: float
    reference_baseline_tmin: float
    reference_baseline_tmax: float
    reference_signal_tmin: float
    reference_signal_tmax: float
    
@dataclass
class PicoamperemeterConfig:
    COM: str

@dataclass
class DAQConfig:
    picoamp: PicoamperemeterConfig
    picoscope: PicoscopeConfig

@dataclass
class Statistics:
  readouts_per_position: int
  reference_period: int


@dataclass
class MeasurementConfig:
    cfg_centre_finder: Centre_find_config
    cfg_grid: CircularConstantDensity_config
    cfg_DAQ: DAQConfig
    cfg_motors: MotorConfig
    cfg_statistics: Statistics
    
