# Import key functions and classes for easier access when users import the package

# Import Data API functions
from .data_api import (
    get_observations,
    get_super_observations,
    get_flying_missions,
    get_mission_launch_site,
    get_predicted_path,
    poll_super_observations
)

# Import Forecasts API functions
from .forecasts_api import (
    get_point_forecasts,
    get_initialization_times,
    get_temperature_2m,
    get_dewpoint_2m,
    get_wind_u_10m, get_wind_v_10m,
    get_pressure_msl,
    get_500hpa_wind_u, get_500hpa_wind_v,
    get_500hpa_geopotential, get_850hpa_geopotential,
    get_500hpa_temperature, get_850hpa_temperature,

    get_historical_temperature_2m,
    get_historical_500hpa_geopotential,
    get_historical_500hpa_wind_u, get_historical_500hpa_wind_v,

    get_tropical_cyclones
)

# Define what should be available when users import *
__all__ = [
    "get_observations",
    "get_super_observations",
    "get_flying_missions",
    "get_mission_launch_site",
    "get_predicted_path",
    "poll_super_observations",

    "get_point_forecasts",
    "get_initialization_times",

    "get_temperature_2m",
    "get_dewpoint_2m",
    "get_wind_u_10m",
    "get_wind_v_10m",
    "get_500hpa_wind_u",
    "get_500hpa_wind_v",
    "get_pressure_msl",
    "get_500hpa_geopotential",
    "get_850hpa_geopotential",
    "get_500hpa_temperature",
    "get_850hpa_temperature",

    "get_historical_temperature_2m",
    "get_historical_500hpa_geopotential",
    "get_historical_500hpa_wind_u",
    "get_historical_500hpa_wind_v",
    "get_tropical_cyclones"
]