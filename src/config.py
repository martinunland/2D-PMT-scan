from dataclasses import dataclass

@dataclass
class Centre_find_config:
    number_profiles: int
    profile_r_start: float
    profile_r_stop: float
    coarse_step: float
    fine_step: float
    fit_results_file: str

@dataclass
class Circular_constant_density_config:
    r_max: float
    r_step: float

@dataclass
class DAQ_config:
    picoscope_primary_channel: str
    picoscope_secondary_channel: str
    COM_motors: list
    COM_picoamperemeter: str

@dataclass
class Paths:
    data_pulse_mode: str
    data_current_mode: str
    centre_testing: str
    log: str

@dataclass
class Measurement_Config:
    cfg_centre_finder: Centre_find_config
    cfg_grid: Circular_constant_density_config
    cfg_DAQ: DAQ_config
    cfg_paths: Paths
    
