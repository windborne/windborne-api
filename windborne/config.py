import os

# current APIs versions and links
DATA_API_BASE_URL = "https://sensor-data.windbornesystems.com/api/v1"
FORECASTS_API_BASE_URL = "https://forecasts.windbornesystems.com/api/v1"

# If not set properly make_api_request will display an error message
CLIENT_ID = os.getenv("WB_CLIENT_ID")
API_KEY = os.getenv("WB_API_KEY")

LAUNCH_SITES = {
    '2af36807-2a03-4a89-a54c-c4a09906215a': 'VD',
    '1d8f0702-bd4f-485c-b461-bac0375bbfdd': 'DC',
    '95dc05e7-ebc2-4127-ae70-6a84cd7c9480': 'WS',
    '72d649c7-6faa-4a12-8c78-3e5e9a149766': 'AL',
    'd06da229-94b2-4a9d-828c-a20d8b3c7e3f': 'NY',
    '97186bc1-0fe5-4dcf-b86a-fd00b3e9ba92': 'FH',
    '7dea0491-a41c-4d49-b371-db2a0babe98c': 'HW',
    'ac69c1de-91d9-4b2f-9a41-6aacec10ddcc': 'OAK',
    'ea9a469a-1f7d-4691-b2ad-73cd04842c42': 'SV',
    '954ddab5-9a0d-48ad-899c-0207f32e123f': 'BW',
    'e6074c13-16ff-42c9-9316-bececf7184b5': 'LAH',
    'd65f0b97-f6e9-49d3-8ae5-89c1efd6690c': 'OKC',
    'dcdba72f-3fb2-4971-9ba1-30df7f67b932': 'FL',
    '90fe9fd7-d656-4943-b57b-c90868cf3ca0': 'FB',
    '51da1d97-4473-466d-96fe-8b2c45462189': 'CB',
    'd504fe5c-e3ec-4c83-87c7-807f63d3aed0': 'PR',
    '7b5867eb-48d7-42c7-8028-346588877e95': 'SC',
    '15a10191-ecc7-42ed-865d-aa2c304be720': 'SK',
    '7489f53d-e937-4098-9666-b735b5ed5a06': 'DAEGU',
    'be90782a-59db-4dc4-bdb5-e41d81c60343': 'KE'
}

# GRIDDED FORECASTS
FORECASTS_GRIDDED_URL = f"{FORECASTS_API_BASE_URL}/gridded"

# HISTORICAL FORECASTS
FORECASTS_HISTORICAL_URL = f"{FORECASTS_API_BASE_URL}/gridded/historical"

# TCS
FORECASTS_TCS_URL = f"{FORECASTS_API_BASE_URL}/tropical_cyclones"
TCS_SUPPORTED_FORMATS = ('.csv', '.json', '.geojson', '.gpx', '.kml', 'little_r')