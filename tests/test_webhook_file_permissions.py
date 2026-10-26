"""Webhook secrets must stay private even when saving the response fails."""

import errno
import json
import os
import stat
from unittest import mock

import pytest

from windborne import webhooks_api as webhooks


RESPONSE = {'id': 42, 'signing_secret': 'synthetic-secret'}


@pytest.mark.skipif(os.name != 'posix', reason='POSIX file permission semantics')
@pytest.mark.parametrize('umask', [0o022, 0o000])
@pytest.mark.parametrize('existing', [False, True])
def test_output_is_private_before_first_write_and_replaces_only_when_complete(
        tmp_path, umask, existing):
    destination = tmp_path / 'response.json'
    if existing:
        destination.write_text('previous response')
        destination.chmod(0o644)
    original_dump = json.dump

    def inspect_first_write(response, output, **kwargs):
        assert stat.S_IMODE(os.fstat(output.fileno()).st_mode) == 0o600
        if existing:
            assert destination.read_text() == 'previous response'
        else:
            assert not destination.exists()
        return original_dump(response, output, **kwargs)

    previous_umask = os.umask(umask)
    try:
        with mock.patch.object(webhooks, 'make_api_request', return_value=RESPONSE) as request:
            with mock.patch.object(webhooks.json, 'dump', side_effect=inspect_first_write):
                assert webhooks.create_webhook(
                    'https://example.com/webhook', output_file=destination,
                ) is RESPONSE
            request.assert_called_once()
    finally:
        os.umask(previous_umask)

    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert json.loads(destination.read_text()) == RESPONSE
    assert list(tmp_path.iterdir()) == [destination]


@pytest.mark.skipif(os.name != 'posix', reason='POSIX file descriptor semantics')
@pytest.mark.parametrize('failure', [
    'open', 'fchmod', 'fdopen', 'serialize', 'serialize_type', 'write', 'flush', 'replace',
])
def test_output_failure_preserves_response_existing_file_and_closes_descriptors(
        tmp_path, monkeypatch, failure):
    destination = tmp_path / 'response.json'
    destination.write_text('previous response')
    destination.chmod(0o644)
    descriptors = []
    original_mkstemp = webhooks.tempfile.mkstemp
    original_fdopen = os.fdopen
    error = TypeError('Synthetic serialization failure') if failure == 'serialize_type' else OSError('Synthetic output failure')

    def tracked_mkstemp(*args, **kwargs):
        if failure == 'open':
            raise error
        descriptor, path = original_mkstemp(*args, **kwargs)
        descriptors.append(descriptor)
        return descriptor, path

    def fail(*args, **kwargs):
        raise error

    def failing_stream(*args, **kwargs):
        stream = original_fdopen(*args, **kwargs)
        monkeypatch.setattr(stream, failure, fail)
        return stream

    monkeypatch.setattr(webhooks.tempfile, 'mkstemp', tracked_mkstemp)
    if failure == 'fchmod':
        monkeypatch.setattr(webhooks.os, 'fchmod', fail)
    elif failure == 'fdopen':
        monkeypatch.setattr(webhooks.os, 'fdopen', fail)
    elif failure.startswith('serialize'):
        monkeypatch.setattr(webhooks.json, 'dump', fail)
    elif failure in ('write', 'flush'):
        monkeypatch.setattr(webhooks.os, 'fdopen', failing_stream)
    elif failure == 'replace':
        monkeypatch.setattr(webhooks.os, 'replace', fail)

    with mock.patch.object(webhooks, 'make_api_request', return_value=RESPONSE) as request:
        with pytest.raises(webhooks.WebhookOutputError) as caught:
            webhooks.create_webhook('https://example.com/webhook', output_file=destination)
        request.assert_called_once()

    assert caught.value.response is RESPONSE
    assert caught.value.__cause__ is error
    assert 'synthetic-secret' not in str(caught.value)
    assert destination.read_text() == 'previous response'
    assert stat.S_IMODE(destination.stat().st_mode) == 0o644
    assert list(tmp_path.iterdir()) == [destination]
    for descriptor in descriptors:
        with pytest.raises(OSError) as closed:
            os.fstat(descriptor)
        assert closed.value.errno == errno.EBADF


@pytest.mark.skipif(os.name != 'posix', reason='POSIX symbolic link and FIFO semantics')
@pytest.mark.parametrize('kind', ['symlink', 'dangling_symlink', 'fifo'])
def test_special_output_paths_are_rejected_before_creation(tmp_path, kind):
    destination = tmp_path / 'response.json'
    target = tmp_path / 'target.json'
    if kind == 'fifo':
        os.mkfifo(str(destination))
    else:
        if kind == 'symlink':
            target.write_text('preserve me')
        destination.symlink_to(target)

    with mock.patch.object(webhooks, 'make_api_request') as request:
        with pytest.raises(OSError):
            webhooks.create_webhook('https://example.com/webhook', output_file=destination)
        request.assert_not_called()
    if kind == 'symlink':
        assert target.read_text() == 'preserve me'
    elif kind == 'dangling_symlink':
        assert not target.exists()


def test_destination_changed_to_symlink_after_request_preserves_response(tmp_path):
    destination = tmp_path / 'response.json'
    target = tmp_path / 'target.json'
    target.write_text('preserve me')

    def api_success(*args, **kwargs):
        destination.symlink_to(target)
        return RESPONSE

    with mock.patch.object(webhooks, 'make_api_request', side_effect=api_success) as request:
        with pytest.raises(webhooks.WebhookOutputError) as caught:
            webhooks.create_webhook('https://example.com/webhook', output_file=destination)
        request.assert_called_once()
    assert caught.value.response is RESPONSE
    assert target.read_text() == 'preserve me'
    assert destination.is_symlink()


def test_unwritable_parent_is_rejected_before_mutation_even_for_existing_file(tmp_path):
    destination = tmp_path / 'response.json'
    destination.write_text('previous response')
    original_access = os.access

    def parent_is_unwritable(path, mode):
        return False if path == tmp_path else original_access(path, mode)

    with mock.patch.object(webhooks.os, 'access', side_effect=parent_is_unwritable):
        with mock.patch.object(webhooks, 'make_api_request') as request:
            with pytest.raises(PermissionError, match='parent is not writable'):
                webhooks.create_webhook('https://example.com/webhook', output_file=destination)
            request.assert_not_called()
    assert destination.read_text() == 'previous response'


def test_cleanup_error_does_not_hide_original_failure_or_successful_response(tmp_path):
    destination = tmp_path / 'response.json'
    original = OSError('Synthetic serialization failure')

    def partial_write_then_fail(response, output, **kwargs):
        output.write('{"signing_secret": "synthetic-secret"')
        raise original

    with mock.patch.object(webhooks, 'make_api_request', return_value=RESPONSE):
        with mock.patch.object(webhooks.json, 'dump', side_effect=partial_write_then_fail):
            with mock.patch.object(webhooks.os, 'unlink', side_effect=OSError('Synthetic cleanup failure')):
                with pytest.raises(webhooks.WebhookOutputError) as caught:
                    webhooks.create_webhook('https://example.com/webhook', output_file=destination)
    assert caught.value.response is RESPONSE
    assert caught.value.__cause__ is original
    assert not destination.exists()
    # Even if cleanup fails, the abandoned file containing the response is private.
    temporary_files = list(tmp_path.iterdir())
    assert len(temporary_files) == 1
    assert 'synthetic-secret' in temporary_files[0].read_text()
    if os.name == 'posix':
        assert stat.S_IMODE(temporary_files[0].stat().st_mode) == 0o600
