import pytest
import requests
import os
from windborne import get_point_forecasts


def test_invalid_point_forecast():
    with pytest.raises(requests.exceptions.HTTPError) as exc_info:
        point_forecasts = get_point_forecasts(
            coordinates=f"0,0",
            min_forecast_hour=0,
            max_forecast_hour=120,
            initialization_time='20100101'
        )
    assert exc_info.value.response.status_code == 500


def test_missing_credentials():
    # Temporarily remove credentials
    original_client_id = os.environ.get('WB_CLIENT_ID')
    original_api_key = os.environ.get('WB_API_KEY')
    
    try:
        if 'WB_CLIENT_ID' in os.environ:
            del os.environ['WB_CLIENT_ID']
        if 'WB_API_KEY' in os.environ:
            del os.environ['WB_API_KEY']
        
        # Reset the cached credentials
        import windborne.api_request
        windborne.api_request.VERIFIED_WB_CLIENT_ID = None
        windborne.api_request.VERIFIED_WB_API_KEY = None
        
        with pytest.raises(ValueError) as exc_info:
            get_point_forecasts(coordinates="0,0")
        
        assert "set your Client ID and API key" in str(exc_info.value)
    
    finally:
        # Restore original credentials
        if original_client_id:
            os.environ['WB_CLIENT_ID'] = original_client_id
        if original_api_key:
            os.environ['WB_API_KEY'] = original_api_key