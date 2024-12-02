import argparse
from . import (
    poll_observations,
    get_observations,
    get_super_observations,
    get_flying_missions,
    get_mission_launch_site,
    get_predicted_path
)

def main():
    parser = argparse.ArgumentParser(description='WindBorne API Command Line Interface')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Poll Observations Command
    poll_parser = subparsers.add_parser('poll-observations', help='Poll observations within a time range')
    poll_parser.add_argument('start_time', help='Starting time (YYYY-MM-DD_HH:MM)')
    poll_parser.add_argument('end_time', nargs='?', help='Ending time (YYYY-MM-DD_HH:MM) | If not specified looking till current time')
    poll_parser.add_argument('output', help='Save output to a single file (filename.csv or filename.json) or to multiple files (csv or little_r)')
    poll_parser.add_argument('-i', '--interval', type=int, default=60, help='Polling interval in seconds')
    poll_parser.add_argument('-b', '--bucket-hours', type=float, default=6.0, help='Hours per bucket')

    # Get Observations Command
    obs_parser = subparsers.add_parser('observations', help='Get observations with filters')
    obs_parser.add_argument('start_time', help='Get observations since this time (YYYY-MM-DD_HH:MM)')
    obs_parser.add_argument('-mt', '--min-time', help='Minimum time filter (YYYY-MM-DD_HH:MM)')
    obs_parser.add_argument('-xt', '--max-time', help='Maximum time filter (YYYY-MM-DD_HH:MM)')
    obs_parser.add_argument('-m', '--mission-id', help='Filter by mission ID')
    obs_parser.add_argument('-ml', '--min-latitude', type=float, help='Minimum latitude filter')
    obs_parser.add_argument('-xl', '--max-latitude', type=float, help='Maximum latitude filter')
    obs_parser.add_argument('-mg', '--min-longitude', type=float, help='Minimum longitude filter')
    obs_parser.add_argument('-xg', '--max-longitude', type=float, help='Maximum longitude filter')
    obs_parser.add_argument('-id', '--include-ids', action='store_true', help='Include observation IDs')
    obs_parser.add_argument('-mn', '--include-mission-name', action='store_true', help='Include mission names')
    obs_parser.add_argument('-u', '--include-updated-at', action='store_true', help='Include update timestamps')
    obs_parser.add_argument('output', nargs='?', help='Output file')

    # Get Super Observations Command
    super_obs_parser = subparsers.add_parser('super-observations', help='Get super observations with filters')
    super_obs_parser.add_argument('start_time', help='Get super observations since this time (YYYY-MM-DD_HH:MM)')
    super_obs_parser.add_argument('-mt', '--min-time', help='Minimum time filter (YYYY-MM-DD_HH:MM)')
    super_obs_parser.add_argument('-xt', '--max-time', help='Maximum time filter (YYYY-MM-DD_HH:MM)')
    super_obs_parser.add_argument('-m', '--mission-id', help='Filter by mission ID')
    super_obs_parser.add_argument('-id', '--include-ids', action='store_true', help='Include observation IDs')
    super_obs_parser.add_argument('-mn', '--include-mission-name', action='store_true', help='Include mission names')
    super_obs_parser.add_argument('-u', '--include-updated-at', action='store_true', help='Include update timestamps')
    super_obs_parser.add_argument('output', nargs='?', help='Output file')

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

    args = parser.parse_args()

    if args.command == 'poll-observations':
        # Error handling is performed within poll_observations
        # and we display the appropriate error messages
        # No need to implement them here

        # In case user wants to save all poll observation data in a single file | filename.format
        if '.' in args.output:
            save_to_file = args.output
            output_format = None
        # In case user wants separate file for each data from missions (buckets)
        else:
            save_to_file = None
            output_format = args.output

        poll_observations(
            start_time=args.start_time,
            end_time=args.end_time,
            interval=args.interval,
            save_to_file=save_to_file,
            bucket_hours=args.bucket_hours,
            output_format=output_format
        )

    elif args.command == 'observations':
        get_observations(
            since=args.start_time,
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

    elif args.command == 'super-observations':
        get_super_observations(
            since=args.start_time,
            min_time=args.min_time,
            max_time=args.max_time,
            include_ids=args.include_ids,
            include_mission_name=args.include_mission_name,
            include_updated_at=args.include_updated_at,
            mission_id=args.mission_id,
            save_to_file=args.output
        )

    elif args.command == 'flying-missions':
        get_flying_missions(cli_mode=True, save_to_file=args.output)

    elif args.command == 'launch-site':
        get_mission_launch_site(
            cli_mode=True,
            mission_id=args.mission_id,
            save_to_file=args.output
        )

    elif args.command == 'predict-path':
        get_predicted_path(
            mission_id=args.mission_id,
            save_to_file=args.output
        )
    else:
        parser.print_help()

if __name__ == '__main__':
    main()