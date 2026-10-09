"""CLI commands for Events, context data, and customer webhook management."""
import argparse
import inspect
import json
import sys

from .events_api import (
    get_events, get_event_index, get_event, get_event_init_times, get_event_context,
)
from .climatology_api import get_climatology
from .weather_context_api import get_weather_context
from .webhooks_api import (
    WebhookOutputError,
    list_webhooks, get_webhook, create_webhook, update_webhook, delete_webhook,
    add_webhook_subscription, update_webhook_subscription,
    delete_webhook_subscription, ping_webhook_subscription,
)


def _boolean(value):
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    raise argparse.ArgumentTypeError('Expected true or false')


def _json_object_file(path):
    try:
        if path == '-':
            value = json.load(sys.stdin)
        else:
            with open(path, encoding='utf-8') as stream:
                value = json.load(stream)
    except (OSError, ValueError) as error:
        raise argparse.ArgumentTypeError('Could not read JSON body: {}'.format(error))
    if not isinstance(value, dict):
        raise argparse.ArgumentTypeError('The request body must be a JSON object')
    return value


def _output(parser, function):
    parser.add_argument('-o', '--output', dest='output_file', help='Save the response to a file instead of printing it')
    parser.set_defaults(_api_function=function, _api_parser=parser)


def _bounds(parser):
    for name in ('min-latitude', 'max-latitude', 'min-longitude', 'max-longitude'):
        parser.add_argument('--' + name, type=float)


def _optional_boolean(parser, name, help):
    parser.add_argument('--' + name, type=_boolean, nargs='?', const=True, help=help)


def add_public_api_commands(subparsers):
    events = subparsers.add_parser('events', help='Query published weather events')
    operations = events.add_subparsers(dest='operation')
    operations.required = True
    event_functions = {
        'list': get_events, 'index': get_event_index, 'detail': get_event,
        'init_times': get_event_init_times, 'context': get_event_context,
    }
    for operation, function in event_functions.items():
        aliases = ['init-times'] if operation == 'init_times' else []
        command = operations.add_parser(operation, aliases=aliases)
        _output(command, function)
        command.add_argument('-m', '--model', default='wm-6')
        if operation in ('list', 'index'):
            command.add_argument('event_type', help='atmospheric_river, heatwave, coldwave, or front')
            _bounds(command)
        elif operation in ('detail', 'init_times'):
            command.add_argument('event_id')
        else:
            command.add_argument('coordinates', help='Semicolon-separated latitude,longitude pairs')
            command.add_argument('--event-type')
            command.add_argument('--min-forecast-time')
            command.add_argument('--max-forecast-time')
        if operation in ('list', 'detail', 'context'):
            command.add_argument('--initialization-time', help='Omit to use the latest published run')
        if operation in ('list', 'detail'):
            command.add_argument('-f', '--format', choices=['json', 'geojson'])
        if operation == 'list':
            _optional_boolean(command, 'include-details', 'Include forecast-hour geometries (true or false)')
        if operation == 'index':
            command.add_argument('--min-time')
            command.add_argument('--max-time')
            command.add_argument('--page', type=int)
            command.add_argument('--page-size', type=int)

    climatology = subparsers.add_parser('climatology', help='Get hourly ERA5 normals for coordinates')
    _output(climatology, get_climatology)
    climatology.add_argument('coordinates', help='Semicolon-separated latitude,longitude pairs')
    climatology.add_argument('--time')
    climatology.add_argument('--start-time')
    climatology.add_argument('--end-time')
    climatology.add_argument('--normal')
    climatology.add_argument('--rolling-average-days', type=int)
    _optional_boolean(climatology, 'elevation-correction', 'Correct temperature and dewpoint for elevation')
    climatology.add_argument('--water-strategy')

    context = subparsers.add_parser('weather_context', help='Get forecasts with optional weather context')
    _output(context, get_weather_context)
    context.add_argument('coordinates', nargs='?', help='Semicolon-separated latitude,longitude pairs')
    context.add_argument('--stations', help='Comma- or semicolon-separated ICAO station IDs')
    context.add_argument('--initialization-time')
    context.add_argument('--min-forecast-time')
    context.add_argument('--max-forecast-time')
    context.add_argument('--min-forecast-hour', type=int)
    context.add_argument('--max-forecast-hour', type=int)
    context.add_argument('--observation-hours', type=int)
    context.add_argument('--climatology-normal')
    for option in ('conditions', 'observations', 'distribution', 'climatology'):
        _optional_boolean(context, 'include-' + option, 'Include {} (true or false)'.format(option))

    webhooks = subparsers.add_parser('webhooks', help='Manage your webhooks and subscriptions')
    operations = webhooks.add_subparsers(dest='operation')
    operations.required = True
    webhook_functions = {
        'list': list_webhooks, 'get': get_webhook, 'create': create_webhook,
        'update': update_webhook, 'delete': delete_webhook,
        'add_subscription': add_webhook_subscription,
        'update_subscription': update_webhook_subscription,
        'delete_subscription': delete_webhook_subscription,
        'ping': ping_webhook_subscription,
    }
    for operation, function in webhook_functions.items():
        aliases = [operation.replace('_', '-')] if '_' in operation else []
        command = operations.add_parser(operation, aliases=aliases)
        _output(command, function)
        if operation == 'list':
            command.add_argument('--page', type=int)
            command.add_argument('--page-size', type=int)
            command.add_argument('--url')
            command.add_argument('--subscription-type')
            _optional_boolean(command, 'active', 'Filter by active state; omit to return all states')
        if operation not in ('list', 'create'):
            command.add_argument('webhook_id')
        if operation in ('update_subscription', 'delete_subscription', 'ping'):
            command.add_argument('subscription_id')
        if operation in ('create', 'update', 'add_subscription', 'update_subscription'):
            command.add_argument('--body', required=True, type=_json_object_file,
                                 help='JSON request-body file; use - to read from stdin')


def run_public_api_command(args):
    """Dispatch commands registered above; leave existing CLI commands alone."""
    function = getattr(args, '_api_function', None)
    if function is None:
        return False
    kwargs = {name: value for name, value in vars(args).items()
              if name not in ('command', 'operation', '_api_function', '_api_parser', 'body')}
    body = getattr(args, 'body', None)
    if body is not None:
        fields = set(inspect.signature(function).parameters) - set(kwargs) - {'print_response'}
        unsupported = set(body) - fields
        if unsupported:
            args._api_parser.error('Unsupported request fields: {}'.format(', '.join(sorted(unsupported))))
        kwargs.update(body)
    kwargs['print_response'] = not kwargs.get('output_file')
    try:
        inspect.signature(function).bind(**kwargs)
    except TypeError as error:
        args._api_parser.error(str(error))
    try:
        function(**kwargs)
    except WebhookOutputError as error:
        # The write succeeded. Preserve the result on the remaining output
        # channel so a CLI caller can recover it without repeating the write.
        print('The API request succeeded, but output failed. Recover the response below; '
              'do not repeat the write.', file=sys.stderr)
        print(json.dumps(error.response, indent=2), file=sys.stderr)
        raise SystemExit(1)
    return True
