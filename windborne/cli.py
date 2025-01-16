import argparse

from . import (
    super_observations,
    observations,
    get_observations_page,
    get_super_observations_page,
    get_flying_missions,
    get_mission_launch_site,
    get_predicted_path,

    get_point_forecasts,
    get_initialization_times,
    get_temperature_2m,
    get_dewpoint_2m,
    get_wind_u_10m, get_wind_v_10m,
    get_500hpa_wind_u, get_500hpa_wind_v,
    get_500hpa_temperature, get_850hpa_temperature,
    get_pressure_msl,
    get_500hpa_geopotential, get_850hpa_geopotential,

    get_historical_temperature_2m,
    get_historical_500hpa_geopotential,
    get_historical_500hpa_wind_u, get_historical_500hpa_wind_v,
    get_tropical_cyclones

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
    super_obs_parser.add_argument('-i', '--interval', type=int, default=60, help='Polling interval in seconds')
    super_obs_parser.add_argument('-b', '--bucket-hours', type=float, default=6.0, help='Hours per bucket')
    super_obs_parser.add_argument('-d', '--output-dir', help='Directory path where the separate files should be saved. If not provided, files will be saved in current directory.')
    super_obs_parser.add_argument('output', help='Save output to a single file (filename.csv, filename.json or filename.little_r) or to multiple files (csv or little_r)')

    # Observations Command
    obs_parser = subparsers.add_parser('observations', help='Poll observations within a time range')
    obs_parser.add_argument('start_time', help='Starting time (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)')
    obs_parser.add_argument('end_time', help='End time (YYYY-MM-DD_HH:MM, "YYYY-MM-DD HH:MM:SS" or YYYY-MM-DDTHH:MM:SS.fffZ)', nargs='?', default=None)
    obs_parser.add_argument('-m', '--mission-id', help='Filter observations by mission ID')
    obs_parser.add_argument('-ml', '--min-latitude', type=float, help='Minimum latitude filter')
    obs_parser.add_argument('-xl', '--max-latitude', type=float, help='Maximum latitude filter')
    obs_parser.add_argument('-mg', '--min-longitude', type=float, help='Minimum longitude filter')
    obs_parser.add_argument('-xg', '--max-longitude', type=float, help='Maximum longitude filter')
    obs_parser.add_argument('-id', '--include-ids', action='store_true', help='Include observation IDs')
    obs_parser.add_argument('-u', '--include-updated-at', action='store_true', help='Include update timestamps')
    obs_parser.add_argument('-i', '--interval', type=int, default=60, help='Polling interval in seconds')
    obs_parser.add_argument('-b', '--bucket-hours', type=float, default=6.0, help='Hours per bucket')
    obs_parser.add_argument('-d', '--output-dir', help='Directory path where the separate files should be saved. If not provided, files will be saved in current directory.')
    obs_parser.add_argument('output', help='Save output to a single file (filename.csv, filename.json or filename.little_r) or to multiple files (csv or little_r)')


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
    super_obs_page_parser.add_argument('-id', '--include-ids', action='store_true', help='Include observation IDs')
    super_obs_page_parser.add_argument('-mn', '--include-mission-name', action='store_true', help='Include mission names')
    super_obs_page_parser.add_argument('-u', '--include-updated-at', action='store_true', help='Include update timestamps')
    super_obs_page_parser.add_argument('output', nargs='?', help='Output file')

    # Get Flying Missions Command
    flying_parser = subparsers.add_parser('flying-missions', help='Get currently flying missions')
    flying_parser.add_argument('output', nargs='?', help='Output file')

    # Get Mission Launch Site Command
    launch_site_parser = subparsers.add_parser('launch-site', help='Get mission launch site')
    launch_site_parser.add_argument('mission_id', help='Mission ID')
    launch_site_parser.add_argument('output', nargs='?', help='Output file')

    # Get Predicted Path Command
    prediction_parser = subparsers.add_parser('predict-path', help='Get predicted flight path')
    prediction_parser.add_argument('mission_id', help='Mission ID')
    prediction_parser.add_argument('output', nargs='?', help='Output file')

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
    points_parser.add_argument('output_file', help='Output file')

    # GRIDDED FORECASTS
    ####################################################################################################################
    # Gridded 2m temperature Command
    gridded_temperature_2m_parser = subparsers.add_parser('grid_temp_2m', help='Get gridded output of global 2m temperature forecasts')
    gridded_temperature_2m_parser.add_argument('args', nargs='*', help='time output_file')

    # Gridded 2m dewpoint Command
    gridded_dewpoint_2m_parser = subparsers.add_parser('grid_dewpoint_2m', help='Get gridded output of global dewpoint forecasts')
    gridded_dewpoint_2m_parser.add_argument('args', nargs='*', help='time output_file')

    # Gridded wind-u 10m Command
    gridded_wind_u_10m_parser = subparsers.add_parser('grid_wind_u_10m', help='Get gridded output of global 10m u-component of wind forecasts')
    gridded_wind_u_10m_parser.add_argument('args', nargs='*', help='time output_file')

    # Gridded wind-v 10m Command
    gridded_wind_v_10m_parser = subparsers.add_parser('grid_wind_v_10m', help='Get gridded output of global 10m v-component of wind forecasts')
    gridded_wind_v_10m_parser.add_argument('args', nargs='*', help='time output_file')

    # Gridded 500hPa wind-u Command
    gridded_500hpa_wind_u_parser = subparsers.add_parser('grid_500hpa_wind_u', help='Get gridded output of global 500hPa wind v-component of wind forecasts')
    gridded_500hpa_wind_u_parser.add_argument('args', nargs='*', help='time output_file')

    # Gridded 500hPa wind-v Command
    gridded_500hpa_wind_v_parser = subparsers.add_parser('grid_500hpa_wind_v', help='Get gridded output of global 500hPa wind u-component of wind forecasts')
    gridded_500hpa_wind_v_parser.add_argument('args', nargs='*', help='time output_file')

    # Gridded 500hPa temperature Command
    gridded_500hpa_temperature_parser = subparsers.add_parser('grid_500hpa_temperature', help='Get gridded output of global 500hPa temperature forecasts')
    gridded_500hpa_temperature_parser.add_argument('args', nargs='*', help='time output_file')

    # Gridded 850hPa temperature Command
    gridded_850hpa_temperature_parser = subparsers.add_parser('grid_850hpa_temperature', help='Get gridded output of global 850hPa temperature forecasts')
    gridded_850hpa_temperature_parser.add_argument('args', nargs='*', help='time output_file')

    # Gridded mean sea level pressure Command
    gridded_pressure_msl_parser = subparsers.add_parser('grid_pressure_msl', help='Get gridded output of global mean sea level pressure forecasts')
    gridded_pressure_msl_parser.add_argument('args', nargs='*', help='time output_file')

    # Gridded 500hPa geopotential Command
    gridded_500hpa_geopotential_parser = subparsers.add_parser('grid_500hpa_geopotential', help='Get gridded output of global 500hPa geopotential forecasts')
    gridded_500hpa_geopotential_parser.add_argument('args', nargs='*', help='time output_file')

    # Gridded 850hPa geopotential Command
    gridded_850hpa_geopotential_parser = subparsers.add_parser('grid_850hpa_geopotential', help='Get gridded output of global 500hPa geopotential forecasts')
    gridded_850hpa_geopotential_parser.add_argument('args', nargs='*', help='time output_file')

    # HISTORICAL FORECASTS
    ####################################################################################################################
    # Historical 500hpa geopotential Command
    historical_temperature_2m_parser = subparsers.add_parser('hist_temp_2m', help='Get historical output of global temperature forecasts')
    historical_temperature_2m_parser.add_argument('args', nargs='*', help='initialization_time forecast_hour output_file')

    # Historical 500hpa geopotential Command
    historical_500hpa_geopotential_parser = subparsers.add_parser('hist_500hpa_geopotential', help='Get historical output of global 500hPa geopotential forecasts')
    historical_500hpa_geopotential_parser.add_argument('args', nargs='*', help='initialization_time forecast_hour output_file')

    # Historical 500hpa wind u Command
    historical_500hpa_wind_u_parser = subparsers.add_parser('hist_500hpa_wind_u', help='Get historical output of global 500hPa wind u forecasts')
    historical_500hpa_wind_u_parser.add_argument('args', nargs='*', help='initialization_time forecast_hour output_file')

    # Historical 500hpa wind v Command
    historical_500hpa_wind_v_parser = subparsers.add_parser('hist_500hpa_wind_v', help='Get historical output of global 500hPa wind v forecasts')
    historical_500hpa_wind_v_parser.add_argument('args', nargs='*', help='initialization_time forecast_hour output_file')

    # OTHER
    # TCS
    ####################################################################################################################

    # Tropical Cyclones Command
    cyclones_parser = subparsers.add_parser('cyclones', help='Get tropical cyclone forecasts')
    cyclones_parser.add_argument('-b', '--basin',  help='Optional: filter tropical cyclones on basin[ NA, EP, WP, NI, SI, AU, SP]')
    cyclones_parser.add_argument('args', nargs='*',
                                 help='[optional: initialization time (YYYYMMDDHH, YYYY-MM-DDTHH, or YYYY-MM-DDTHH:mm:ss)] output_file')

    # Initialization Times Command
    initialization_times_parser = subparsers.add_parser('init_times', help='Get available initialization times for point forecasts')


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
            save_to_file = args.output
            output_format = None
            output_dir = None
        # In case user wants separate file for each data from missions (buckets)
        else:
            save_to_file = None
            output_format = args.output
            output_dir = args.output_dir

        super_observations(
            start_time=args.start_time,
            end_time=args.end_time,
            interval=args.interval,
            save_to_file=save_to_file,
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
            save_to_file = args.output
            output_format = None
            output_dir = None
        # In case user wants separate file for each data from missions (buckets)
        else:
            save_to_file = None
            output_format = args.output
            output_dir = args.output_dir

        observations(
            start_time=args.start_time,
            end_time=args.end_time,
            include_ids=args.include_ids,
            include_updated_at=args.include_updated_at,
            mission_id=args.mission_id,
            min_latitude=args.min_latitude,
            max_latitude=args.max_latitude,
            min_longitude=args.min_longitude,
            max_longitude=args.max_longitude,
            interval=args.interval,
            save_to_file=save_to_file,
            bucket_hours=args.bucket_hours,
            output_dir=output_dir,
            output_format=output_format
        )

    elif args.command == 'observations-page':
        if not args.output:
            pprint(get_observations_page(
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
            ))
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
                save_to_file=args.output
            )

    elif args.command == 'super-observations-page':
        if not args.output:
            pprint(get_super_observations_page(
                since=args.since,
                min_time=args.min_time,
                max_time=args.max_time,
                include_ids=args.include_ids,
                include_mission_name=args.include_mission_name,
                include_updated_at=args.include_updated_at,
                mission_id=args.mission_id
            ))
        else:
            get_super_observations_page(
                since=args.since,
                min_time=args.min_time,
                max_time=args.max_time,
                include_ids=args.include_ids,
                include_mission_name=args.include_mission_name,
                include_updated_at=args.include_updated_at,
                mission_id=args.mission_id,
                save_to_file=args.output
            )

    elif args.command == 'flying-missions':
        get_flying_missions(cli=True, save_to_file=args.output)

    elif args.command == 'launch-site':
        get_mission_launch_site(
            mission_id=args.mission_id,
            save_to_file=args.output
        )

    elif args.command == 'predict-path':
        get_predicted_path(
            mission_id=args.mission_id,
            save_to_file=args.output
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
            save_to_file=args.output_file
        )

    elif args.command == 'init_times':
        if get_initialization_times():
            print("Available initialization times for point forecasts:\n")
            pprint(get_initialization_times())
        else:
            print("We can't currently display available initialization times for point forecasts:\n")

    elif args.command == 'grid_temp_2m':
        # Parse grid_temp_2m arguments
        if len(args.args) in [0,1]:
            print("To get the gridded output of global 2m temperature forecast you need to provide the time for which to get the forecast and an output file.")
            print("\nUsage: windborne grid_temp_2m time output_file")
        elif len(args.args) == 2:
            get_temperature_2m(time=args.args[0], save_to_file=args.args[1])
        else:
            print("Too many arguments")
            print("\nUsage: windborne grid_temp_2m time output_file")

    elif args.command == 'grid_dewpoint_2m':
        # Parse grid_dewpoint_2m arguments
        if len(args.args) in [0,1]:
            print(f"To get the gridded output of global 2m dew point forecast you need to provide the time for which to get the forecast and an output file.")
            print("\nUsage: windborne grid_dewpoint_2m time output_file")
        elif len(args.args) == 2:
            get_dewpoint_2m(time=args.args[0], save_to_file=args.args[1])
        else:
            print("Too many arguments")
            print("\nUsage: windborne grid_dewpoint_2m time output_file")

    elif args.command == 'grid_wind_u_10m':
        # Parse grid_wind_u_10m arguments
        if len(args.args) in [0,1]:
            print(f"To get the gridded output of global 10m u-component of wind forecasts you need to provide the time for which to get the forecast and an output file.")
            print("\nUsage: windborne grid_wind_u_10m time output_file")
        elif len(args.args) == 2:
            get_wind_u_10m(time=args.args[0], save_to_file=args.args[1])
        else:
            print("Too many arguments")
            print("\nUsage: windborne grid_wind_u_10m time output_file")

    elif args.command == 'grid_wind_v_10m':
        # Parse grid_wind_v_10m arguments
        if len(args.args) in [0,1]:
            print(f"To get the gridded output of global 10m v-component of wind forecasts you need to provide the time for which to get the forecast and an output file.")
            print("\nUsage: windborne grid_wind_v_10m time output_file")
        elif len(args.args) == 2:
            get_wind_v_10m(time=args.args[0], save_to_file=args.args[1])
        else:
            print("Too many arguments")
            print("\nUsage: windborne grid_wind_v_10m time output_file")

    elif args.command == 'grid_500hpa_wind_u':
        # Parse grid_500hpa_wind_u arguments
        if len(args.args) in [0,1]:
            print(f"To get the gridded output of global 500hPa u-component of wind forecasts you need to provide the time for which to get the forecast and an output file.")
            print("\nUsage: windborne grid_500hpa_wind_u time output_file")
        elif len(args.args) == 2:
            get_500hpa_wind_u(time=args.args[0], save_to_file=args.args[1])
        else:
            print("Too many arguments")
            print("\nUsage: windborne grid_500hpa_wind_u time output_file")

    elif args.command == 'grid_500hpa_wind_v':
        # Parse grid_500hpa_wind_v arguments
        if len(args.args) in [0,1]:
            print(f"To get the gridded output of global 500hPa v-component of wind forecasts you need to provide the time for which to get the forecast and an output file.")
            print("\nUsage: windborne grid_500hpa_wind_v time output_file")
        elif len(args.args) == 2:
            get_500hpa_wind_v(time=args.args[0], save_to_file=args.args[1])
        else:
            print("Too many arguments")
            print("\nUsage: windborne grid_500hpa_wind_v time output_file")

    elif args.command == 'grid_500hpa_temperature':
        # Parse grid_500hpa_temperature arguments
        if len(args.args) in [0,1]:
            print(f"To get the gridded output of global 500hPa temperature forecasts you need to provide the time for which to get the forecast and an output file.")
            print("\nUsage: windborne grid_500hpa_temperature time output_file")
            return
        elif len(args.args) == 2:
            get_500hpa_temperature(time=args.args[0], save_to_file=args.args[1])
        else:
            print("Too many arguments")
            print("\nUsage: windborne grid_500hpa_temperature time output_file")

    elif args.command == 'grid_850hpa_temperature':
        # Parse grid_850hpa_temperature arguments
        if len(args.args) in [0,1]:
            print(f"To get the gridded output of global 850hPa temperature forecasts you need to provide the time for which to get the forecast and an output file.")
            print("\nUsage: windborne grid_850hpa_temperature time output_file")
            return
        elif len(args.args) == 2:
            get_850hpa_temperature(time=args.args[0], save_to_file=args.args[1])
        else:
            print("Too many arguments")
            print("\nUsage: windborne grid_850hpa_temperature time output_file")

    elif args.command == 'grid_pressure_msl':
        # Parse grid_pressure_msl arguments
        if len(args.args) in [0,1]:
            print(f"To get the gridded output of global mean sea level pressure forecasts you need to provide the time for which to get the forecast and an output file.")
            print("\nUsage: windborne grid_pressure_msl time output_file")
        elif len(args.args) == 2:
            get_pressure_msl(time=args.args[0], save_to_file=args.args[1])
        else:
            print("Too many arguments")
            print("\nUsage: windborne grid_pressure_msl time output_file")

    elif args.command == 'grid_500hpa_geopotential':
        # Parse grid_500hpa_geopotential arguments
        if len(args.args) in [0,1]:
            print(f"To get the gridded output of global 500hPa geopotential forecasts you need to provide the time for which to get the forecast and an output file.")
            print("\nUsage: windborne grid_500hpa_geopotential time output_file")
            return
        elif len(args.args) == 2:
            get_500hpa_geopotential(time=args.args[0], save_to_file=args.args[1])
        else:
            print("Too many arguments")
            print("\nUsage: windborne grid_500hpa_geopotential time output_file")

    elif args.command == 'grid_850hpa_geopotential':
        # Parse grid_850hpa_geopotential arguments
        if len(args.args) in [0,1]:
            print(f"To get the gridded output of global 850hPa geopotential forecasts you need to provide the time for which to get the forecast and an output file.")
            print("\nUsage: windborne grid_850hpa_geopotential time output_file")
            return
        elif len(args.args) == 2:
            get_850hpa_geopotential(time=args.args[0], save_to_file=args.args[1])
        else:
            print("Too many arguments")
            print("\nUsage: windborne grid_850hpa_geopotential time output_file")

    # HISTORICAL

    elif args.command == 'hist_temp_2m':
        # Parse historical temperature arguments
        if len(args.args) in [0,1,2]:
            print("To get the historical output of global temperature forecasts you need to provide\n"
                  "  - initialization time of the forecast\n"
                  "  - How many hours after the run time the forecast is valid at\n"
                  "  - An ouput file to save the data")
            print("\nUsage: windborne hist_temp_2m initialization_time forecast_hour output_file")
            return
        elif len(args.args) == 3:
            get_historical_temperature_2m(initialization_time=args.args[0], forecast_hour=args.args[1], save_to_file=args.args[2])
        else:
            print("Too many arguments")
            print("\nUsage: windborne hist_temp_2m initialization_time forecast_hour output_file")

    elif args.command == 'hist_500hpa_geopotential':
        # Parse historical 500 hpa geopotential arguments
        if len(args.args) in [0,1,2]:
            print("To get the historical output of global 500hPa geopotential forecasts you need to provide\n"
                  "  - initialization time of the forecast\n"
                  "  - How many hours after the run time the forecast is valid at\n"
                  "  - An ouput file to save the data")
            print("\nUsage: windborne hist_500hpa_geopotential initialization_time forecast_hour output_file")
            return
        elif len(args.args) == 3:
            get_historical_500hpa_geopotential(initialization_time=args.args[0], forecast_hour=args.args[1], save_to_file=args.args[2])
        else:
            print("Too many arguments")
            print("\nUsage: windborne hist_500hpa_geopotential initialization_time forecast_hour output_file")

    elif args.command == 'hist_500hpa_wind_u':
        if len(args.args) in [0,1,2]:
            print("To get the historical output of global 500hPa wind u forecasts you need to provide\n"
                  "  - initialization time of the forecast\n"
                  "  - How many hours after the run time the forecast is valid at\n"
                  "  - An ouput file to save the data")
            print("\nUsage: windborne hist_500hpa_wind_u initialization_time forecast_hour output_file")
        elif len(args.args) == 3:
            get_historical_500hpa_wind_u(initialization_time=args.args[0], forecast_hour=args.args[1], save_to_file=args.args[2])
        else:
            print("Too many arguments")
            print("\nUsage: windborne hist_500hpa_wind_u initialization_time forecast_hour output_file")

    elif args.command == 'hist_500hpa_wind_v':
        if len(args.args) in [0,1,2]:
            print("To get the historical output of global 500hPa wind v forecasts you need to provide\n"
                  "  - initialization time of the forecast\n"
                  "  - How many hours after the run time the forecast is valid at\n"
                  "  - An ouput file to save the data")
            print("\nUsage: windborne hist_500hpa_wind_u initialization_time forecast_hour output_file")
        elif len(args.args) == 3:
            get_historical_500hpa_wind_v(initialization_time=args.args[0], forecast_hour=args.args[1], save_to_file=args.args[2])
        else:
            print("Too many arguments")
            print("\nUsage: windborne hist_500hpa_wind_v initialization_time forecast_hour output_file")

    elif args.command == 'cyclones':
        # Parse cyclones arguments
        basin_name = 'ALL basins'
        if args.basin:
            basin_name = f"{args.basin} basin"
            print(f"Checking for tropical cyclones only within {args.basin} basin\n")

        if len(args.args) == 0:
            print("Loading tropical cyclones for our latest available initialization time\n")
            if get_tropical_cyclones(basin=args.basin):
                print(f"Found {len(get_tropical_cyclones())} cyclone(s)\n")
                pprint(get_tropical_cyclones(basin=args.basin))
                return
            else:
                print("There are no active tropical cyclones for our latest available initialization time.")
        elif len(args.args) == 1:
            if '.' in args.args[0]:
                # Save tcs with the latest available initialization time in filename
                get_tropical_cyclones(basin=args.basin, save_to_file=args.args[0])
            else:
                # Display tcs for selected initialization time
                if get_tropical_cyclones(initialization_time=args.args[0], basin=args.basin):
                    print(f"Loading tropical cyclones for initialization time {args.args[0]}\n")
                    print(f"Found {len(get_tropical_cyclones(initialization_time=args.args[0]))} cyclone(s)\n")
                    pprint(get_tropical_cyclones(initialization_time=args.args[0], basin=args.basin))
                else:
                    print(f"No active tropical cyclones for {basin_name} and {args.args[0]} initialization time.")
        elif len(args.args) == 2:
            print(f"Saving tropical cyclones for initialization time {args.args[0]} and {basin_name}\n")
            get_tropical_cyclones(initialization_time=args.args[0], basin=args.basin, save_to_file=args.args[1])
        else:
            print("Error: Too many arguments")
            print("Usage: windborne cyclones [initialization_time] output_file")

    else:
        parser.print_help()

if __name__ == '__main__':
    main()