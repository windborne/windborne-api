import copy
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from windborne import observations_api


class ObservationPrintAliasesTest(unittest.TestCase):
    cases = [
        (
            "get_flying_missions", (), "print_results",
            {"missions": [{"id": "mission", "name": "W-123"}]},
            [{"id": "mission", "name": "W-123"}],
        ),
        (
            "get_mission_launch_site", ("mission",), "print_result",
            {"launch_site": {"id": "site", "latitude": 0, "longitude": 1}},
            {"id": "site", "latitude": 0, "longitude": 1},
        ),
        (
            "get_predicted_path", ("mission",), "print_result",
            {"prediction": [{"time": "2026-10-01T00:00:00Z", "latitude": 0,
                             "longitude": 1, "altitude": 100}]},
            [{"time": "2026-10-01T00:00:00Z", "latitude": 0,
              "longitude": 1, "altitude": 100}],
        ),
        (
            "get_current_location", ("mission",), "print_result",
            {"latitude": 0, "longitude": 1, "altitude": 100},
            {"latitude": 0, "longitude": 1, "altitude": 100},
        ),
        (
            "get_flight_path", ("mission",), "print_result",
            {"flight_data": [{"transmit_time": "2026-10-01T00:00:00Z",
                              "latitude": 0, "longitude": 1, "altitude": 100}]},
            [{"transmit_time": "2026-10-01T00:00:00Z",
              "latitude": 0, "longitude": 1, "altitude": 100}],
        ),
        (
            "get_constellation_status", (), "print_results",
            {"missions": [{"id": "mission", "name": "W-123", "latitude": 0,
                           "longitude": 1, "altitude": 100, "ascent_rate": 2}]},
            [{"id": "mission", "name": "W-123", "latitude": 0,
              "longitude": 1, "altitude": 100, "ascent_rate": 2}],
        ),
        (
            "get_soundings", (), "print_results",
            {"soundings": [{"id": "sounding", "mission_id": "mission",
                            "start_time": "2026-10-01T00:00:00Z",
                            "end_time": "2026-10-01T01:00:00Z",
                            "min_altitude_m": 0, "max_altitude_m": 5000}]},
            [{"id": "sounding", "mission_id": "mission",
              "start_time": "2026-10-01T00:00:00Z",
              "end_time": "2026-10-01T01:00:00Z",
              "min_altitude_m": 0, "max_altitude_m": 5000}],
        ),
        (
            "get_sounding", ("sounding",), "print_result",
            {"sounding_id": "sounding", "mission_id": "mission", "data": []},
            {"sounding_id": "sounding", "mission_id": "mission", "data": []},
        ),
    ]

    def call_with_output(self, name, args, response, **kwargs):
        output = io.StringIO()
        with patch.object(observations_api, "make_api_request",
                          return_value=copy.deepcopy(response)) as request:
            with patch.object(observations_api, "get_flying_mission",
                              return_value={"id": "mission", "name": "W-123"}):
                with redirect_stdout(output):
                    result = getattr(observations_api, name)(*args, **kwargs)
        request.assert_called_once()
        # Printing is a client-side option, never an HTTP query parameter.
        params = request.call_args[1].get("params", {})
        self.assertFalse({"print_result", "print_results", "print_response"} & set(params))
        return result, output.getvalue()

    def test_documented_alias_prints_same_response_as_legacy_keyword(self):
        for name, args, legacy, response, expected in self.cases:
            with self.subTest(helper=name):
                old_result, old_output = self.call_with_output(
                    name, args, response, **{legacy: True}
                )
                result, output = self.call_with_output(
                    name, args, response, print_response=True
                )
                self.assertEqual(expected, result)
                self.assertEqual(old_result, result)
                self.assertTrue(output)
                self.assertEqual(old_output, output)

    def test_explicit_alias_takes_precedence_and_default_stays_quiet(self):
        for name, args, legacy, response, expected in self.cases:
            with self.subTest(helper=name):
                for options in ({}, {legacy: True, "print_response": False}):
                    result, output = self.call_with_output(name, args, response, **options)
                    self.assertEqual(expected, result)
                    self.assertEqual("", output)
                result, output = self.call_with_output(
                    name, args, response, **{legacy: False, "print_response": True}
                )
                self.assertEqual(expected, result)
                self.assertTrue(output)

    def test_existing_positional_print_options_keep_their_positions(self):
        for name, args, legacy, response, expected in self.cases:
            with self.subTest(helper=name):
                if name == "get_soundings":
                    positional = (None,) * 12 + (True,)
                elif name == "get_current_location":
                    positional = ("mission", None, True, False)
                else:
                    positional = args + (None, True)
                result, output = self.call_with_output(name, positional, response)
                self.assertEqual(expected, result)
                self.assertTrue(output)


class ObservationRequestOptionsTest(unittest.TestCase):
    @patch.object(observations_api, "make_api_request")
    def test_sounding_length_is_forwarded_in_meters_including_zero(self, request):
        request.return_value = {"soundings": [{"id": "sounding"}]}
        for minimum in (0, 1500.5):
            with self.subTest(min_length=minimum):
                result = observations_api.get_soundings(
                    min_length=minimum, min_altitude=0, page=0, page_size=20
                )
                request.assert_called_with(
                    observations_api.DATA_API_BASE_URL + "/soundings",
                    params={"min_altitude": 0, "min_length": minimum,
                            "page": 0, "page_size": 20},
                )
                self.assertEqual([{"id": "sounding"}], result)
        observations_api.get_soundings()
        self.assertNotIn("min_length", request.call_args[1]["params"])

    @patch.object(observations_api, "make_api_request")
    def test_asos_high_frequency_flag_preserves_other_filters_and_response(self, request):
        response = {"station": {"icao": "KDFW"}, "observations": [{"temperature_2m": 25}]}
        request.return_value = response
        for requested, encoded in ((True, "true"), (False, "false")):
            with self.subTest(include_high_frequency=requested):
                result = observations_api.get_recent_asos_observations(
                    "KDFW", 12, "2026-10-01T00:00:00Z", None, False,
                    include_high_frequency=requested,
                )
                request.assert_called_with(
                    observations_api.DATA_API_BASE_URL + "/asos/recent",
                    params={"station": "KDFW", "hours": 12,
                            "since": "2026-10-01T00:00:00Z",
                            "include_high_frequency": encoded},
                )
                self.assertIs(response, result)
        observations_api.get_recent_asos_observations("KDFW")
        request.assert_called_with(
            observations_api.DATA_API_BASE_URL + "/asos/recent",
            params={"station": "KDFW"},
        )


if __name__ == "__main__":
    unittest.main()
