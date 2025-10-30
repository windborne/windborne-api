# Import key functions and classes for easier access when users import the package

# Import API request helpers
from .api_request import API_BASE_URL, make_api_request

# Import Data API functions
from .data_api import (
    get_observations_page,
    get_observations,

    get_super_observations_page,
    get_super_observations,

    poll_super_observations,
    poll_observations,

    get_flying_missions,
    get_mission_launch_site,
    get_predicted_path,
    get_current_location,
    get_flight_path
)

# Import Forecasts API functions
from .forecasts_api import (
    get_point_forecasts,
    get_point_forecasts_interpolated,
    get_initialization_times,
    get_archived_initialization_times,
    get_run_information,
    get_variables,

    get_gridded_forecast,
    get_full_gridded_forecast,

    get_tropical_cyclones,

    get_population_weighted_hdd,
    get_population_weighted_cdd
)

# Define what should be available when users import *
__all__ = [
    "get_observations_page",
    "get_observations",

    "get_super_observations_page",
    "get_super_observations",

    "poll_super_observations",
    "poll_observations",

    "get_flying_missions",
    "get_mission_launch_site",
    "get_predicted_path",
    "get_current_location",
    "get_flight_path",

    "get_point_forecasts",
    "get_point_forecasts_interpolated",
    "get_initialization_times",
    "get_archived_initialization_times",
    "get_run_information",
    "get_variables",
    
    "get_gridded_forecast",
    "get_full_gridded_forecast",
    
    "get_tropical_cyclones",

    "get_population_weighted_hdd",
    "get_population_weighted_cdd",

    # API helpers
    "API_BASE_URL",
    "make_api_request",
]