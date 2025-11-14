import argparse
import json

from . import (
    get_super_observations,
    get_observations,

    get_observations_page,
    get_super_observations_page,

    poll_super_observations,
    poll_observations,

    get_flying_missions,
    get_mission_launch_site,
    get_predicted_path,
    get_current_location,
    get_flight_path,

    get_point_forecasts,
    get_point_forecasts_interpolated,
    get_initialization_times,
    get_archived_initialization_times,
    get_run_information,
    get_variables,
    get_gridded_forecast,
    get_tropical_cyclones,
    get_population_weighted_hdd,
    get_population_weighted_cdd

)

from pprint import pprint

def main():
    parser = argparse.ArgumentParser(description='WindBorne API Command Line Interface')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    ####################################################################################################################
    # DATA API FUNCTIONS
    ####################################################################################################################
    # Super Observations Command
    super_obs_parser = subparsers.add_parser('super-observations', help='Poll super observations within a time range')
    super_obs_parser.add_argument('start_time', help='Starting time (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)')
    super_obs_parser.add_argument('end_time', help='End time (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)', nargs='?', default=None)
    super_obs_parser.add_argument('-b', '--bucket-hours', type=float, default=6.0, help='Hours per bucket')
    super_obs_parser.add_argument('-d', '--output-dir', help='Directory path where the separate files should be saved. If not provided, files will be saved in current directory.')
    super_obs_parser.add_argument('-m', '--mission-id', help='Filter by mission ID')
    super_obs_parser.add_argument('output', help='Save output to a single file (filename.csv, filename.json or filename.little_r) or to or to multiple files (csv, json, netcdf or little_r)')

    # Observations Command
    obs_parser = subparsers.add_parser('observations', help='Poll observations within a time range')
    obs_parser.add_argument('start_time', help='Starting time (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)')
    obs_parser.add_argument('end_time', help='End time (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)', nargs='?', default=None)
    obs_parser.add_argument('-m', '--mission-id', help='Filter observations by mission ID')
    obs_parser.add_argument('-ml', '--min-latitude', type=float, help='Minimum latitude filter')
    obs_parser.add_argument('-xl', '--max-latitude', type=float, help='Maximum latitude filter')
    obs_parser.add_argument('-mg', '--min-longitude', type=float, help='Minimum longitude filter')
    obs_parser.add_argument('-xg', '--max-longitude', type=float, help='Maximum longitude filter')
    obs_parser.add_argument('-u', '--include-updated-at', action='store_true', help='Include update timestamps')
    obs_parser.add_argument('-b', '--bucket-hours', type=float, default=6.0, help='Hours per bucket')
    obs_parser.add_argument('-d', '--output-dir', help='Directory path where the separate files should be saved. If not provided, files will be saved in current directory.')
    obs_parser.add_argument('output', help='Save output to a single file (filename.csv, filename.json or filename.little_r) or to multiple files (csv, json, netcdf or little_r)')


    # Get Observations Page Command
    obs_page_parser = subparsers.add_parser('observations-page', help='Get observations page with filters')
    obs_page_parser.add_argument('since', help='Get observations since this time (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)')
    obs_page_parser.add_argument('-mt', '--min-time', help='Minimum time filter (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)')
    obs_page_parser.add_argument('-xt', '--max-time', help='Maximum time filter (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)')
    obs_page_parser.add_argument('-m', '--mission-id', help='Filter by mission ID')
    obs_page_parser.add_argument('-ml', '--min-latitude', type=float, help='Minimum latitude filter')
    obs_page_parser.add_argument('-xl', '--max-latitude', type=float, help='Maximum latitude filter')
    obs_page_parser.add_argument('-mg', '--min-longitude', type=float, help='Minimum longitude filter')
    obs_page_parser.add_argument('-xg', '--max-longitude', type=float, help='Maximum longitude filter')
    obs_page_parser.add_argument('-id', '--include-ids', action='store_true', help='Include observation IDs')
    obs_page_parser.add_argument('-mn', '--include-mission-name', action='store_true', help='Include mission names')
    obs_page_parser.add_argument('-u', '--include-updated-at', action='store_true', help='Include update timestamps')
    obs_page_parser.add_argument('output', nargs='?', help='Output file')

    # Get Super Observations Command
    super_obs_page_parser = subparsers.add_parser('super-observations-page', help='Get super observations page with filters')
    super_obs_page_parser.add_argument('since', help='Get super observations page since this time (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)')
    super_obs_page_parser.add_argument('-mt', '--min-time', help='Minimum time filter (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)')
    super_obs_page_parser.add_argument('-xt', '--max-time', help='Maximum time filter (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)')
    super_obs_page_parser.add_argument('-m', '--mission-id', help='Filter by mission ID')
    super_obs_page_parser.add_argument('-mn', '--include-mission-name', action='store_true', help='Include mission names')
    super_obs_page_parser.add_argument('-u', '--include-updated-at', action='store_true', help='Include update timestamps')
    super_obs_page_parser.add_argument('output', nargs='?', help='Output file')

    # Poll Super Observations Command
    poll_super_obs_parser = subparsers.add_parser('poll-super-observations', help='Continuously polls for super observations and saves to files in specified format.')
    poll_super_obs_parser.add_argument('start_time', help='Starting time (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)')
    poll_super_obs_parser.add_argument('-b', '--bucket-hours', type=float, default=6.0, help='Hours per bucket')
    poll_super_obs_parser.add_argument('-d', '--output-dir', help='Directory path where the separate files should be saved. If not provided, files will be saved in current directory.')
    poll_super_obs_parser.add_argument('-m', '--mission-id', help='Filter observations by mission ID')
    poll_super_obs_parser.add_argument('output', help='Save output to multiple files (csv, json, netcdf or little_r)')

    # Poll Observations Command
    poll_obs_parser = subparsers.add_parser('poll-observations', help='Continuously polls for observations and saves to files in specified format.')
    poll_obs_parser.add_argument('start_time', help='Starting time (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)')
    poll_obs_parser.add_argument('-m', '--mission-id', help='Filter observations by mission ID')
    poll_obs_parser.add_argument('-ml', '--min-latitude', type=float, help='Minimum latitude filter')
    poll_obs_parser.add_argument('-xl', '--max-latitude', type=float, help='Maximum latitude filter')
    poll_obs_parser.add_argument('-mg', '--min-longitude', type=float, help='Minimum longitude filter')
    poll_obs_parser.add_argument('-xg', '--max-longitude', type=float, help='Maximum longitude filter')
    poll_obs_parser.add_argument('-u', '--include-updated-at', action='store_true', help='Include update timestamps')
    poll_obs_parser.add_argument('-b', '--bucket-hours', type=float, default=6.0, help='Hours per bucket')
    poll_obs_parser.add_argument('-d', '--output-dir', help='Directory path where the separate files should be saved. If not provided, files will be saved in current directory.')
    poll_obs_parser.add_argument('output', help='Save output to multiple files (csv, json, netcdf or little_r)')

    # Get Flying Missions Command
    flying_parser = subparsers.add_parser('flying-missions', help='Get currently flying missions')
    flying_parser.add_argument('output', nargs='?', help='Output file')

    # Get Mission Launch Site Command
    launch_site_parser = subparsers.add_parser('launch-site', help='Get mission launch site')
    launch_site_parser.add_argument('mission_id', help='Mission ID')
    launch_site_parser.add_argument('output', nargs='?', help='Output file')

    # Get Current Location Command
    current_location_parser = subparsers.add_parser('current-location', help='Get current location')
    current_location_parser.add_argument('mission_id', help='Mission ID')
    current_location_parser.add_argument('output', nargs='?', help='Output file')

    # Get Predicted Path Command
    prediction_parser = subparsers.add_parser('predict-path', help='Get predicted flight path')
    prediction_parser.add_argument('mission_id', help='Mission ID')
    prediction_parser.add_argument('output', nargs='?', help='Output file')

    # Get Flight Path Command
    flight_path_parser = subparsers.add_parser('flight-path', help='Get traveled flight path')
    flight_path_parser.add_argument('mission_id', help='Mission ID')
    flight_path_parser.add_argument('output', nargs='?', help='Output file')

    ####################################################################################################################
    # FORECASTS API FUNCTIONS
    ####################################################################################################################
   
    # Points Forecast Command
    # We have quite a few quite a few optional query parameters here
    # so we set coordinates and output_file to required instead of
    # setting all args into a parser arg (add_argument('args', nargs='*', ...)
    points_parser = subparsers.add_parser('points', help='Get the forecast at a given point or set of points')
    points_parser.add_argument('coordinates', help='Coordinate pairs in format "latitudeA,longitudeA; latitudeB,longitudeB"')
    points_parser.add_argument('-mt','--min-time', help='Minimum forecast time')
    points_parser.add_argument('-xt','--max-time', help='Maximum forecast time')
    points_parser.add_argument('-mh','--min-hour', type=int, help='Minimum forecast hour')
    points_parser.add_argument('-xh','--max-hour', type=int, help='Maximum forecast hour')
    points_parser.add_argument('-i', '--init-time', help='Initialization time')
    points_parser.add_argument('-m', '--model', default='wm', help='Forecast model (e.g., wm, wm4)')
    points_parser.add_argument('output_file', nargs='?', help='Output file')

    # Interpolated Points Forecast Command
    points_interpolated_parser = subparsers.add_parser('points_interpolated', help='Get interpolated forecast at given point(s)')
    points_interpolated_parser.add_argument('coordinates', help='Coordinate pairs in format "latitudeA,longitudeA; latitudeB,longitudeB"')
    points_interpolated_parser.add_argument('-mt','--min-time', help='Minimum forecast time')
    points_interpolated_parser.add_argument('-xt','--max-time', help='Maximum forecast time')
    points_interpolated_parser.add_argument('-mh','--min-hour', type=int, help='Minimum forecast hour')
    points_interpolated_parser.add_argument('-xh','--max-hour', type=int, help='Maximum forecast hour')
    points_interpolated_parser.add_argument('-i', '--init-time', help='Initialization time')
    points_interpolated_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')
    points_interpolated_parser.add_argument('-m', '--model', default='wm', help='Forecast model (e.g., wm, wm4)')
    points_interpolated_parser.add_argument('output_file', nargs='?', help='Output file (.csv or .json)')

    # GRIDDED FORECASTS
    ####################################################################################################################
    gridded_parser = subparsers.add_parser('gridded', help='Get gridded forecast for a variable')
    gridded_parser.add_argument('args', nargs='*', help='variable time output_file')
    gridded_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')
    gridded_parser.add_argument('-m', '--model', default='wm', help='Forecast model (e.g., wm, wm4, wm4-intra, ecmwf-det)')

    # OTHER
    # TCS
    ####################################################################################################################

    # Tropical Cyclones Command
    tropical_cyclones_parser = subparsers.add_parser('tropical_cyclones', help='Get tropical cyclone forecasts')
    tropical_cyclones_parser.add_argument('-b', '--basin',  help='Optional: filter tropical cyclones on basin[ NA, EP, WP, NI, SI, AU, SP]')
    tropical_cyclones_parser.add_argument('-m', '--model', default='wm', help='Forecast model (e.g., wm, wm4, wm4-intra, ecmwf-det)')
    tropical_cyclones_parser.add_argument('args', nargs='*',
                                 help='[optional: initialization time (YYYYMMDDHH, YYYY-MM-DDTHH, or YYYY-MM-DDTHH:mm:ss)] output_file')

    # Population Weighted HDD Command
    hdd_parser = subparsers.add_parser('hdd', help='Get population weighted heating degree days (HDD) forecasts')
    hdd_parser.add_argument('initialization_time', help='Initialization time (YYYYMMDDHH, YYYY-MM-DDTHH, or YYYY-MM-DDTHH:mm:ss)')
    hdd_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')
    hdd_parser.add_argument('-m', '--model', default='wm', help='Forecast model (e.g., wm, wm4, wm4-intra, ecmwf-det)')
    hdd_parser.add_argument('-o', '--output', help='Output file (supports .csv and .json formats)')

    # Population Weighted CDD Command
    cdd_parser = subparsers.add_parser('cdd', help='Get population weighted cooling degree days (CDD) forecasts')
    cdd_parser.add_argument('initialization_time', help='Initialization time (YYYYMMDDHH, YYYY-MM-DDTHH, or YYYY-MM-DDTHH:mm:ss)')
    cdd_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')
    cdd_parser.add_argument('-m', '--model', default='wm', help='Forecast model (e.g., wm, wm4, wm4-intra, ecmwf-det)')
    cdd_parser.add_argument('-o', '--output', help='Output file (supports .csv and .json formats)')

    # Initialization Times Command
    initialization_times_parser = subparsers.add_parser('init_times', help='Get available initialization times for point forecasts')
    initialization_times_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')
    initialization_times_parser.add_argument('-m', '--model', default='wm', help='Forecast model (e.g., wm, wm4, wm4-intra, ecmwf-det)')

    # Archived Initialization Times Command
    archived_initialization_times_parser = subparsers.add_parser('archived_init_times', help='Get available archived initialization times')
    archived_initialization_times_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')
    archived_initialization_times_parser.add_argument('-m', '--model', default='wm', help='Forecast model (e.g., wm, wm4, wm4-intra, ecmwf-det)')
    archived_initialization_times_parser.add_argument('-p', '--page-end', help='End of page window (ISO 8601). Lists times back 7 days.')

    # Run Information Command
    run_information_parser = subparsers.add_parser('run_information', help='Get run information for a model run')
    run_information_parser.add_argument('initialization_time', help='Initialization time (ISO 8601)')
    run_information_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')
    run_information_parser.add_argument('-m', '--model', default='wm', help='Forecast model (e.g., wm, wm4, wm4-intra, ecmwf-det)')

    # Variables Command
    variables_parser = subparsers.add_parser('variables', help='Get available variables for a model')
    variables_parser.add_argument('-m', '--model', default='wm', help='Forecast model (e.g., wm, wm4, wm4-intra, ecmwf-det)')

    args = parser.parse_args()

    ####################################################################################################################
    # DATA API FUNCTIONS CALLED
    ####################################################################################################################
    if args.command == 'super-observations':
        # Error handling is performed within super_observations
        # and we display the appropriate error messages
        # No need to implement them here

        # In case user wants to save all poll observation data in a single file | filename.format
        if '.' in args.output:
            output_file = args.output
            output_format = None
            output_dir = None
        # In case user wants separate file for each data from missions (buckets)
        else:
            output_file = None
            output_format = args.output
            output_dir = args.output_dir

        get_super_observations(
            start_time=args.start_time,
            end_time=args.end_time,
            output_file=output_file,
            mission_id=args.mission_id,
            bucket_hours=args.bucket_hours,
            output_dir=output_dir,
            output_format=output_format
        )

    elif args.command == 'poll-super-observations':
        output_format = args.output
        output_dir = args.output_dir

        poll_super_observations(
            start_time=args.start_time,
            mission_id=args.mission_id,
            bucket_hours=args.bucket_hours,
            output_dir=output_dir,
            output_format=output_format
        )

    elif args.command == 'poll-observations':
        output_format = args.output
        output_dir = args.output_dir

        poll_observations(
            start_time=args.start_time,
            include_updated_at=args.include_updated_at,
            mission_id=args.mission_id,
            min_latitude=args.min_latitude,
            max_latitude=args.max_latitude,
            min_longitude=args.min_longitude,
            max_longitude=args.max_longitude,
            bucket_hours=args.bucket_hours,
            output_dir=output_dir,
            output_format=output_format
        )

    elif args.command == 'observations':
        # Error handling is performed within observations
        # and we display the appropriate error messages
        # No need to implement them here

        # In case user wants to save all poll observation data in a single file | filename.format
        if '.' in args.output:
            output_file = args.output
            output_format = None
            output_dir = None
        # In case user wants separate file for each data from missions (buckets)
        else:
            output_file = None
            output_format = args.output
            output_dir = args.output_dir

        get_observations(
            start_time=args.start_time,
            end_time=args.end_time,
            include_updated_at=args.include_updated_at,
            mission_id=args.mission_id,
            min_latitude=args.min_latitude,
            max_latitude=args.max_latitude,
            min_longitude=args.min_longitude,
            max_longitude=args.max_longitude,
            output_file=output_file,
            bucket_hours=args.bucket_hours,
            output_dir=output_dir,
            output_format=output_format
        )

    elif args.command == 'observations-page':
        if not args.output:
            print(json.dumps(get_observations_page(
                since=args.since,
                min_time=args.min_time,
                max_time=args.max_time,
                include_ids=args.include_ids,
                include_mission_name=args.include_mission_name,
                include_updated_at=args.include_updated_at,
                mission_id=args.mission_id,
                min_latitude=args.min_latitude,
                max_latitude=args.max_latitude,
                min_longitude=args.min_longitude,
                max_longitude=args.max_longitude
            ), indent=4))
        else:
            get_observations_page(
                since=args.since,
                min_time=args.min_time,
                max_time=args.max_time,
                include_ids=args.include_ids,
                include_mission_name=args.include_mission_name,
                include_updated_at=args.include_updated_at,
                mission_id=args.mission_id,
                min_latitude=args.min_latitude,
                max_latitude=args.max_latitude,
                min_longitude=args.min_longitude,
                max_longitude=args.max_longitude,
                output_file=args.output
            )

    elif args.command == 'super-observations-page':
        if not args.output:
            print(json.dumps(get_super_observations_page(
                since=args.since,
                min_time=args.min_time,
                max_time=args.max_time,
                include_ids=args.include_ids,
                include_mission_name=args.include_mission_name,
                include_updated_at=args.include_updated_at,
                mission_id=args.mission_id
            ), indent=4))
        else:
            get_super_observations_page(
                since=args.since,
                min_time=args.min_time,
                max_time=args.max_time,
                include_ids=args.include_ids,
                include_mission_name=args.include_mission_name,
                include_updated_at=args.include_updated_at,
                mission_id=args.mission_id,
                output_file=args.output
            )

    elif args.command == 'flying-missions':
        get_flying_missions(output_file=args.output, print_results=(not args.output))

    elif args.command == 'launch-site':
        get_mission_launch_site(
            mission_id=args.mission_id,
            output_file=args.output,
            print_result=(not args.output)
        )
    elif args.command == 'current-location':
        get_current_location(
            mission_id=args.mission_id,
            output_file=args.output,
            print_result=(not args.output)
        )
    elif args.command == 'predict-path':
        get_predicted_path(
            mission_id=args.mission_id,
            output_file=args.output,
            print_result=(not args.output)
        )

    elif args.command == 'flight-path':
        get_flight_path(
            mission_id=args.mission_id,
            output_file=args.output,
            print_result=(not args.output)
        )


    ####################################################################################################################
    # FORECASTS API FUNCTIONS CALLED
    ####################################################################################################################
    elif args.command == 'points':
        min_forecast_time = args.min_time if args.min_time else None
        max_forecast_time = args.max_time if args.max_time else None
        min_forecast_hour = args.min_hour if args.min_hour else None
        max_forecast_hour = args.max_hour if args.max_hour else None
        initialization_time = args.init_time if args.init_time else None

        get_point_forecasts(
            coordinates=args.coordinates,
            min_forecast_time=min_forecast_time,
            max_forecast_time=max_forecast_time,
            min_forecast_hour=min_forecast_hour,
            max_forecast_hour=max_forecast_hour,
            initialization_time=initialization_time,
            output_file=args.output_file,
            model=args.model,
            print_response=(not args.output_file)
        )

    elif args.command == 'points_interpolated':
        min_forecast_time = args.min_time if args.min_time else None
        max_forecast_time = args.max_time if args.max_time else None
        min_forecast_hour = args.min_hour if args.min_hour else None
        max_forecast_hour = args.max_hour if args.max_hour else None
        initialization_time = args.init_time if args.init_time else None

        get_point_forecasts_interpolated(
            coordinates=args.coordinates,
            min_forecast_time=min_forecast_time,
            max_forecast_time=max_forecast_time,
            min_forecast_hour=min_forecast_hour,
            max_forecast_hour=max_forecast_hour,
            initialization_time=initialization_time,
            ensemble_member=getattr(args, 'ens_member', None),
            output_file=args.output_file,
            model=args.model,
            print_response=(not args.output_file)
        )

    elif args.command == 'init_times':
        get_initialization_times(print_response=True, ensemble_member=args.ens_member, model=args.model)

    elif args.command == 'archived_init_times':
        get_archived_initialization_times(print_response=True, ensemble_member=args.ens_member, model=args.model, page_end=getattr(args, 'page_end', None))

    elif args.command == 'run_information':
        get_run_information(initialization_time=args.initialization_time, ensemble_member=getattr(args, 'ens_member', None), model=args.model, print_response=True)

    elif args.command == 'variables':
        get_variables(print_response=True, model=args.model)

    elif args.command == 'gridded':
        if len(args.args) in [0,1,2]:
            print(f"To get the gridded forecast for a variable you need to provide the variable, time (or initialization time and forecast hour), and an output file.")
            print(f"\nUsage: windborne gridded variable time output_file or")
            print(f"\n       windborne gridded variable initialization_time forecast_hour output_file")
            print(f"\n       windborne gridded variable level time output_file")
            print(f"\n       windborne gridded variable level initialization_time forecast_hour output_file")
        elif len(args.args) == 3:
            get_gridded_forecast(variable=args.args[0], time=args.args[1], output_file=args.args[2], ensemble_member=args.ens_member, model=args.model)
        elif len(args.args) == 4:
            # Support both historical form: variable initialization_time forecast_hour output
            # and alternate "variable level time output" form by detecting numeric level
            a0, a1, a2, a3 = args.args
            is_level = False
            try:
                # Simple numeric check; levels are integers like 500, 850, 1000
                int(a1)
                is_level = True
            except Exception:
                is_level = False

            # Basic heuristic to detect time-like strings for a2
            def looks_like_time(s: str) -> bool:
                return (
                    (len(s) == 10 and s.isdigit()) or  # YYYYMMDDHH
                    ('T' in s and '-' in s)            # ISO-like
                )

            if is_level and looks_like_time(a2):
                # Map to level/variable with time
                get_gridded_forecast(variable=f"{a1}/{a0}", time=a2, output_file=a3, ensemble_member=args.ens_member, model=args.model)
            else:
                get_gridded_forecast(variable=a0, initialization_time=a1, forecast_hour=a2, output_file=a3, ensemble_member=args.ens_member, model=args.model)
        elif len(args.args) == 5:
            # Support historical variable level syntax:
            #   windborne gridded variable level initialization_time forecast_hour output_file
            a0, a1, a2, a3, a4 = args.args
            try:
                int(a1)
                # Treat a1 as level
                get_gridded_forecast(variable=f"{a1}/{a0}", initialization_time=a2, forecast_hour=a3, output_file=a4, ensemble_member=args.ens_member, model=args.model)
            except Exception:
                # Fallback: treat like variable initialization_time forecast_hour output_file (ignore a1)
                get_gridded_forecast(variable=a0, initialization_time=a2, forecast_hour=a3, output_file=a4, ensemble_member=args.ens_member, model=args.model)
        else:
            print("Too many arguments")

    elif args.command == 'tropical_cyclones':
        # Parse cyclones arguments
        basin_name = 'all basins'
        if args.basin:
            basin_name = f"{args.basin} basin"

        if len(args.args) == 0:
            get_tropical_cyclones(basin=args.basin, print_response=True, model=args.model)
            return
        elif len(args.args) == 1:
            if '.' in args.args[0]:
                # Save tcs with the latest available initialization time in filename
                get_tropical_cyclones(basin=args.basin, output_file=args.args[0], model=args.model)
            else:
                # Display tcs for selected initialization time
                get_tropical_cyclones(initialization_time=args.args[0], basin=args.basin, print_response=True, model=args.model)
        elif len(args.args) == 2:
            print(f"Saving tropical cyclones for initialization time {args.args[0]} and {basin_name}\n")
            get_tropical_cyclones(initialization_time=args.args[0], basin=args.basin, output_file=args.args[1], model=args.model)
        else:
            print("Error: Too many arguments")
            print("Usage: windborne tropical_cyclones [initialization_time] output_file")

    elif args.command == 'hdd':
        # Handle population weighted HDD
        get_population_weighted_hdd(
            initialization_time=args.initialization_time,
            ens_member=args.ens_member,
            output_file=args.output,
            model=args.model,
            print_response=(not args.output)
        )

    elif args.command == 'cdd':
        # Handle population weighted CDD
        get_population_weighted_cdd(
            initialization_time=args.initialization_time,
            ens_member=args.ens_member,
            output_file=args.output,
            model=args.model,
            print_response=(not args.output)
        )

    else:
        parser.print_help()

if __name__ == '__main__':
    main()
