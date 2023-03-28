from dataclasses import dataclass

@dataclass
class CircularConstantDensity_config:
    r_max: float
    r_step: float

@dataclass
class CentreFindConfig:
    ang_step: int
    profile_r_start: float
    profile_r_stop: float
    save_all_profiles: bool
    coarse_step: float
    fine_step: float
    fit_results_file: str
    PMT_bulb_radius: float

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
    count_per_read: int
    primary_channel: int
    reference_channel: int

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
    cfg_centre_finder: CentreFindConfig
    cfg_grid: CircularConstantDensity_config
    cfg_DAQ: DAQConfig
    cfg_motors: MotorConfig
    cfg_statistics: Statistics
    
