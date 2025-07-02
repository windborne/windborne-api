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
    get_initialization_times,
    get_forecast_hours,
    get_generation_times,
    get_full_gridded_forecast,
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
    points_parser.add_argument('output_file', nargs='?', help='Output file')

    # GRIDDED FORECASTS
    ####################################################################################################################
    gridded_parser = subparsers.add_parser('gridded', help='Get gridded forecast for a variable')
    gridded_parser.add_argument('args', nargs='*', help='variable time output_file')
    gridded_parser.add_argument('-i', '--intracycle', action='store_true', help='Use the intracycle forecast')
    gridded_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')

    hist_gridded_parser = subparsers.add_parser('hist_gridded', help='Get historical gridded forecast for a variable')
    hist_gridded_parser.add_argument('args', nargs='*', help='variable initialization_time forecast_hour output_file')
    hist_gridded_parser.add_argument('-i', '--intracycle', action='store_true', help='Use the intracycle forecast')
    hist_gridded_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')

    full_gridded_parser = subparsers.add_parser('grid_full', help='Get full gridded forecast')
    full_gridded_parser.add_argument('args', nargs='*', help='time output_file')

    # Define variables for gridded forecasts - the command name will be derived from the variable name
    # except for special cases like temperature_2m -> temp_2m
    gridded_variables = [
        'temperature_2m',
        'dewpoint_2m',
        'wind_u_10m',
        'wind_v_10m',
        'pressure_msl',
        '500/temperature',
        '500/wind_u',
        '500/wind_v',
        '500/geopotential',
        '850/temperature',
        '850/geopotential'
    ]

    gridded_human_names = {
        'temperature_2m': '2m temperature',
        'dewpoint_2m': '2m dewpoint',
        'wind_u_10m': '10m u-component of wind',
        'wind_v_10m': '10m v-component of wind',
    }

    gridded_forecast_mapping = {}
    for var in gridded_variables:
        cmd_name = var.replace('/', 'hpa_')
        if var == 'temperature_2m':
            cmd_name = 'temp_2m'

        human_name = gridded_human_names.get(var, var)
        if '/' in var:
            level, real_var = var.split('/')
            human_name = f"{level}hPa {real_var}"

        gridded_forecast_mapping[cmd_name] = {
            'variable': var,
            'human_name': human_name
        }

    # Dynamically create parsers for gridded forecasts
    for cmd_name, config in gridded_forecast_mapping.items():
        grid_help = f"Get gridded output of global {config['human_name']} forecasts"
        grid_parser = subparsers.add_parser(f'grid_{cmd_name}', help=grid_help)
        grid_parser.add_argument('args', nargs='*', help='time output_file')
        grid_parser.add_argument('-i', '--intracycle', action='store_true', help='Use the intracycle forecast')
        grid_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')
        grid_parser.set_defaults(variable=config['variable'])

        hist_help = f"Get historical output of global {config['human_name']} forecasts"
        hist_parser = subparsers.add_parser(f'hist_{cmd_name}', help=hist_help)
        hist_parser.add_argument('args', nargs='*', help='initialization_time forecast_hour output_file')
        hist_parser.add_argument('-i', '--intracycle', action='store_true', help='Use the intracycle forecast')
        hist_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')
        hist_parser.set_defaults(variable=config['variable'])

    # OTHER
    # TCS
    ####################################################################################################################

    # Tropical Cyclones Command
    tropical_cyclones_parser = subparsers.add_parser('tropical_cyclones', help='Get tropical cyclone forecasts')
    tropical_cyclones_parser.add_argument('-b', '--basin',  help='Optional: filter tropical cyclones on basin[ NA, EP, WP, NI, SI, AU, SP]')
    tropical_cyclones_parser.add_argument('args', nargs='*',
                                 help='[optional: initialization time (YYYYMMDDHH, YYYY-MM-DDTHH, or YYYY-MM-DDTHH:mm:ss)] output_file')

    # Population Weighted HDD Command
    hdd_parser = subparsers.add_parser('hdd', help='Get population weighted heating degree days (HDD) forecasts')
    hdd_parser.add_argument('initialization_time', help='Initialization time (YYYYMMDDHH, YYYY-MM-DDTHH, or YYYY-MM-DDTHH:mm:ss)')
    hdd_parser.add_argument('-i', '--intracycle', action='store_true', help='Use the intracycle forecast')
    hdd_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')
    hdd_parser.add_argument('-m', '--external-model', help='External model (eg gfs, ifs, hrrr, aifs)')
    hdd_parser.add_argument('-o', '--output', help='Output file (supports .csv and .json formats)')

    # Population Weighted CDD Command
    cdd_parser = subparsers.add_parser('cdd', help='Get population weighted cooling degree days (CDD) forecasts')
    cdd_parser.add_argument('initialization_time', help='Initialization time (YYYYMMDDHH, YYYY-MM-DDTHH, or YYYY-MM-DDTHH:mm:ss)')
    cdd_parser.add_argument('-i', '--intracycle', action='store_true', help='Use the intracycle forecast')
    cdd_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')
    cdd_parser.add_argument('-m', '--external-model', help='External model (eg gfs, ifs, hrrr, aifs)')
    cdd_parser.add_argument('-o', '--output', help='Output file (supports .csv and .json formats)')

    # Initialization Times Command
    initialization_times_parser = subparsers.add_parser('init_times', help='Get available initialization times for point forecasts')
    initialization_times_parser.add_argument('-i', '--intracycle', action='store_true', help='Use the intracycle forecast')
    initialization_times_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')

    # Forecast Hours Command
    forecast_hours_parser = subparsers.add_parser('forecast_hours', help='Get available forecast hours for WeatherMesh')
    forecast_hours_parser.add_argument('-i', '--intracycle', action='store_true', help='Use the intracycle forecast')
    forecast_hours_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')

    # Output Creation Times Command
    output_creation_times_parser = subparsers.add_parser('generation_times', help='Get the time at which each forecast hour output file was generated')
    output_creation_times_parser.add_argument('-i', '--intracycle', action='store_true', help='Use the intracycle forecast')
    output_creation_times_parser.add_argument('-e', '--ens-member', help='Ensemble member (eg 1 or mean)')

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
            print_response=(not args.output_file)
        )

    elif args.command == 'init_times':
        get_initialization_times(print_response=True, ensemble_member=args.ens_member, intracycle=args.intracycle)

    elif args.command == 'forecast_hours':
        get_forecast_hours(print_response=True, ensemble_member=args.ens_member, intracycle=args.intracycle)

    elif args.command == 'generation_times':
        get_generation_times(print_response=True, ensemble_member=args.ens_member, intracycle=args.intracycle)

    elif args.command == 'gridded':
        if len(args.args) in [0,1,2]:
            print(f"To get the gridded forecast for a variable you need to provide the variable, time, and an output file.")
            print(f"\nUsage: windborne gridded variable time output_file")
        elif len(args.args) == 3:
            get_gridded_forecast(variable=args.args[0], time=args.args[1], output_file=args.args[2], ensemble_member=args.ens_member, intracycle=args.intracycle)
        else:
            print("Too many arguments")

    elif args.command == 'grid_full':
        if len(args.args) in [0,1]:
            print("To get the full gridded forecast you need to provide the time for which to get the forecast and an output file.")
            print("\nUsage: windborne grid_full time output_file")
        elif len(args.args) == 2:
            get_full_gridded_forecast(time=args.args[0], output_file=args.args[1])
        else:
            print("Too many arguments")
            print("\nUsage: windborne grid_full time output_file")

    elif args.command == 'hist_gridded':
        if len(args.args) in [0,1,2,3]:
            print(f"To get the historical gridded forecast for a variable you need to provide the variable, initialization time, forecast hour, and an output file.")
            print(f"\nUsage: windborne hist_gridded variable initialization_time forecast_hour output_file")
        elif len(args.args) == 4:
            get_gridded_forecast(variable=args.args[0], initialization_time=args.args[1], forecast_hour=args.args[2], output_file=args.args[3], ensemble_member=args.ens_member, intracycle=args.intracycle)
        else:
            print("Too many arguments")
            print(f"\nUsage: windborne hist_gridded variable initialization_time forecast_hour output_file")

    # Handle all gridded forecast commands
    elif args.command.startswith('grid_'):
        cmd_name = args.command[5:]  # Remove 'grid_' prefix
        if cmd_name in gridded_forecast_mapping:
            if len(args.args) in [0,1]:
                print(f"To get {gridded_forecast_mapping[cmd_name]['human_name']} you need to provide the time for which to get the forecast and an output file.")
                print(f"\nUsage: windborne {args.command} time output_file")
            elif len(args.args) == 2:
                get_gridded_forecast(variable=args.variable, time=args.args[0], output_file=args.args[1], ensemble_member=args.ens_member, intracycle=args.intracycle)
            else:
                print("Too many arguments")
                print(f"\nUsage: windborne {args.command} time output_file")

    # Handle all historical forecast commands
    elif args.command.startswith('hist_'):
        cmd_name = args.command[5:]  # Remove 'hist_' prefix
        if cmd_name in gridded_forecast_mapping:
            if len(args.args) in [0,1,2]:
                print(f"To get {gridded_forecast_mapping[cmd_name]['human_name']} you need to provide\n"
                      "  - initialization time of the forecast\n"
                      "  - How many hours after the initialization time the forecast is valid at\n"
                      "  - An output file to save the data")
                print(f"\nUsage: windborne {args.command} initialization_time forecast_hour output_file")
            elif len(args.args) == 3:
                get_gridded_forecast(variable=args.variable, initialization_time=args.args[0], forecast_hour=args.args[1], output_file=args.args[2], ensemble_member=args.ens_member, intracycle=args.intracycle)
            else:
                print("Too many arguments")
                print(f"\nUsage: windborne {args.command} initialization_time forecast_hour output_file")

    elif args.command == 'tropical_cyclones':
        # Parse cyclones arguments
        basin_name = 'all basins'
        if args.basin:
            basin_name = f"{args.basin} basin"

        if len(args.args) == 0:
            get_tropical_cyclones(basin=args.basin, print_response=True)
            return
        elif len(args.args) == 1:
            if '.' in args.args[0]:
                # Save tcs with the latest available initialization time in filename
                get_tropical_cyclones(basin=args.basin, output_file=args.args[0])
            else:
                # Display tcs for selected initialization time
                get_tropical_cyclones(initialization_time=args.args[0], basin=args.basin, print_response=True)
        elif len(args.args) == 2:
            print(f"Saving tropical cyclones for initialization time {args.args[0]} and {basin_name}\n")
            get_tropical_cyclones(initialization_time=args.args[0], basin=args.basin, output_file=args.args[1])
        else:
            print("Error: Too many arguments")
            print("Usage: windborne tropical_cyclones [initialization_time] output_file")

    elif args.command == 'hdd':
        # Handle population weighted HDD
        get_population_weighted_hdd(
            initialization_time=args.initialization_time, 
            intracycle=args.intracycle,
            ens_member=args.ens_member,
            external_model=args.external_model,
            output_file=args.output,
            print_response=(not args.output)
        )

    elif args.command == 'cdd':
        # Handle population weighted CDD
        get_population_weighted_cdd(
            initialization_time=args.initialization_time, 
            intracycle=args.intracycle,
            ens_member=args.ens_member,
            external_model=args.external_model,
            output_file=args.output,
            print_response=(not args.output)
        )

    else:
        parser.print_help()

if __name__ == '__main__':
    main()
