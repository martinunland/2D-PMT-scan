from dataclasses import dataclass

@dataclass
class Circular_constant_density_config:
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
class Motor_config:
    COM_motors: list
    z_at_PMT_centre: float
    PMT_curvature_mapping: str

@dataclass
class Picoscope_config:
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
class Picoamperemeter_config:
    COM: str

@dataclass
class DAQ_config:
    picoamp: Picoamperemeter_config
    picoscope: Picoscope_config

@dataclass
class Statistics:
  readouts_per_position: int
  reference_period: int


@dataclass
class Measurement_Config:
    cfg_centre_finder: Centre_find_config
    cfg_grid: Circular_constant_density_config
    cfg_DAQ: DAQ_config
    cfg_motors: Motor_config
    cfg_statistics: Statistics
    
