"""Exercise buffered CLI output through a real pipe, with HTTP blocked."""

import json
import os
from pathlib import Path
import subprocess
import sys


def test_closed_stdout_pipe_recovers_created_webhook_without_retry(tmp_path):
    body = tmp_path / 'webhook.json'
    body.write_text(json.dumps({'url': 'https://example.com/webhook'}))
    script = '''
import sys
from unittest.mock import patch
import requests
from windborne import cli, webhooks_api

response = {'id': 42, 'signing_secret': 'synthetic-secret'}
call_count = 0

def create(*args, **kwargs):
    global call_count
    call_count += 1
    return response

sys.argv = ['windborne', 'webhooks', 'create', '--body', sys.argv[1]]
try:
    with patch.object(webhooks_api, 'make_api_request', side_effect=create):
        with patch.object(requests.Session, 'request', side_effect=AssertionError('HTTP is blocked')):
            cli.main()
finally:
    print('API_CALL_COUNT={}'.format(call_count), file=sys.stderr, flush=True)
'''
    environment = os.environ.copy()
    environment.pop('PYTHONUNBUFFERED', None)
    read_fd, write_fd = os.pipe()
    # Closing before the child starts makes the broken pipe deterministic.
    os.close(read_fd)
    try:
        result = subprocess.run(
            [sys.executable, '-c', script, str(body)],
            cwd=str(Path(__file__).resolve().parents[1]),
            env=environment, stdout=write_fd, stderr=subprocess.PIPE,
            text=True, timeout=30,
        )
    finally:
        os.close(write_fd)

    assert result.returncode == 1, result.stderr
    assert 'The API request succeeded, but output failed.' in result.stderr
    assert 'do not repeat the write.' in result.stderr
    response_start = result.stderr.index('{')
    response, _ = json.JSONDecoder().raw_decode(result.stderr[response_start:])
    assert response == {'id': 42, 'signing_secret': 'synthetic-secret'}
    assert result.stderr.count('API_CALL_COUNT=1') == 1
    assert 'Exception ignored' not in result.stderr
