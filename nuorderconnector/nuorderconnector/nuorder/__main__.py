"""Package for making HTTP requests to the NuOrder API

It's recommended to put hostname and consumer/oauth settings in an INI-style
file at the location ~/.config/nuorder.ini. This way you don't have to
put them in for every request.

        [sandbox]
        hostname = wholesale.sandbox1.nuorder.com
        consumer_key = QDaGd4ppfXTPEaxnjz4C
        consumer_secret = ZvbKP5jxL0iBJ2p7zNRsBzG9vo8XdSIVLb1fMkWFX55dsKTL
        oauth_token = 74SCldgh0DfBufxKJTlEe
        oauth_token_secret = Eb6haktmLIeTYO0LuyCktJNADpYPMnvo6rWWKOs6oh1WJH
        app_name = My app

Then you can simply issue a request to their API like this::

    nuorder get /api/companies/codes/list

Please note that the config section name `sandbox` is the
default and can be overridden by passing in `-c <name>`.
Useful when one wants to make calls to both sandbox and production
environments.
"""
import functools
import json
import logging
import sys
import termcolor

import IPython
import argh
import requests
import traitlets

import nuorder
from nuorder import ini_config


def _failure(err):
    return termcolor.colored(str(err), 'red')


def _set_log_level(log_level):
    if log_level is not None:
        level = getattr(logging, log_level.upper())
        logging.basicConfig()
        nuorder.logger.setLevel(level)


DEFAULT_WRAPPED_ERRORS = [
    ini_config.ConfigKeyMissing,
    requests.exceptions.HTTPError,
]


@argh.wrap_errors([ini_config.ConfigKeyMissing], processor=_failure)
@argh.arg('-c', '--config-section')
def interact(
    hostname = None,            # : 'E.g. wholesale.sandbox1.nuorder.com for sandbox'
    consumer_key = None,        # : 'The consumer key to use'
    consumer_secret = None,     # : 'The oauth shared secret to use'
    oauth_token = None,         # : 'OAuth token'
    oauth_token_secret = None,  # : 'OAuth token secret'
    config_section = 'sandbox', # : 'The name of the config section to get settings from.'
    log_level = None            # : 'The log level to use.'
):
    """
    Starts an IPython REPL to enable easy interaction with the NuOrder API
    """
    _set_log_level(log_level)
    c = functools.partial(ini_config.get, config_section)

    nu = nuorder.NuOrder(
        hostname=hostname or c('hostname'),
        consumer_key=consumer_key or c('consumer_key'),
        consumer_secret=consumer_secret or c('consumer_secret'),
        oauth_token=oauth_token or c('oauth_token'),
        oauth_token_secret=oauth_token_secret or c('oauth_token_secret'),
    )

    banner1 = """Welcome to the `nuorder` client interactive mode
Available vars:
    {additional_arg}
    `nuorder` - An instantiation of the nuorder.NuOrder class

Example usage:
    schemas = nuorder.get('/api/schemas')
    products = nuorder.get('/api/products')
    {additional_arg_example}

Notes:
    * Official NuOrder docs can be found online here:
      https://nuorderapi1.docs.apiary.io/
    * Creation of oauth tokens can't be done inside this mode. Please see `nuorder initiate --help`.
"""
    IPython.embed(
        user_ns={'nuorder': nu},
        banner1=banner1,
        config=traitlets.config.Config(colors='LightBG')
    )


@argh.wrap_errors(DEFAULT_WRAPPED_ERRORS, processor=_failure)
@argh.arg('-c', '--config-section')
@argh.arg('--dry-run')
def initiate(
    hostname = None,            # : 'E.g. wholesale.sandbox1.nuorder.com for sandbox'
    consumer_key = None,        # : 'The consumer key to use'
    consumer_secret = None,     # : 'The oauth shared secret to use'
    app_name = None,            # : 'The application name.'
    config_section = 'sandbox', # : 'The name of the config section to get settings from.'
    log_level = None,           # : 'The log level to use.'
    dry_run = False             # : "Don't actually run command, just show what would be run."
):
    """Generate a new oauth token and secret

    Interactive command that requires you to go to the NuOrder admin
    page and confirm the request.
    """
    _set_log_level(log_level)

    c = functools.partial(ini_config.get, config_section)

    base_kwargs = {
        'hostname': hostname or c('hostname'),
        'consumer_key': consumer_key or c('consumer_key'),
        'consumer_secret': consumer_secret or c('consumer_secret'),
    }

    nu = nuorder.NuOrder(
        **base_kwargs,
        oauth_token='',
        oauth_token_secret='',
    )

    resp_json = nu.oauth_initiate(app_name or c('app_name'), dry_run=dry_run)
    resp_text = json.dumps(resp_json, indent=2)

    if 'request_error' in resp_json:
        sys.exit(_failure(resp_text))

    print('Got response:', resp_text, file=sys.stderr)

    if dry_run:
        sys.exit()

    print(
        "Now go to the API management section of NuOrder's admin page "
        "and approve the pending application that matches the details above. "
        "Copy the verification code that was shown in the pop-up after the "
        "approval was made and paste it here.",
        file=sys.stderr
    )
    verifier = input("Verification code [paste and press Enter]: ")

    nu = nuorder.NuOrder(
        **base_kwargs,
        oauth_token=resp_json['oauth_token'],
        oauth_token_secret=resp_json['oauth_token_secret'],
    )
    resp_json = nu.oauth_token_request(verifier, dry_run=dry_run)

    if 'request_error' in resp_json:
        sys.exit(_failure(json.dumps(resp_json, indent=2)))

    print(
        'Success! Final OAuth token and secret to use below. '
        'Remember to save them in the INI config.',
        file=sys.stderr
    )
    return json.dumps(resp_json, indent=2)


@argh.wrap_errors(DEFAULT_WRAPPED_ERRORS, processor=_failure)
@argh.arg('-c', '--config-section')
@argh.arg('--dry-run')
def delete(
    endpoint,                   # : 'The endpoint to interact with.'
    hostname = None,            # : 'E.g. wholesale.sandbox1.nuorder.com for sandbox'
    consumer_key = None,        # : 'The consumer key to use'
    consumer_secret = None,     # : 'The oauth shared secret to use'
    oauth_token = None,         # : 'OAuth token'
    oauth_token_secret = None,  # : 'OAuth token secret'
    config_section = 'sandbox', # : 'The name of the config section to get settings from.'
    log_level = None,           # : 'The log level to use.'
    dry_run = False             # : "Don't actually run command, just show what would be run."
):
    """Make a DELETE request to NuOrder"""
    _set_log_level(log_level)

    c = functools.partial(ini_config.get, config_section)

    nu = nuorder.NuOrder(
        hostname=hostname or c('hostname'),
        consumer_key=consumer_key or c('consumer_key'),
        consumer_secret=consumer_secret or c('consumer_secret'),
        oauth_token=oauth_token or c('oauth_token'),
        oauth_token_secret=oauth_token_secret or c('oauth_token_secret'),
    )
    resp_json = nu.delete(endpoint, dry_run=dry_run)
    return json.dumps(resp_json, indent=2)


@argh.wrap_errors(DEFAULT_WRAPPED_ERRORS, processor=_failure)
@argh.arg('-c', '--config-section')
@argh.arg('--dry-run')
def get(
    endpoint,                   # : 'The endpoint to interact with.'
    hostname = None,            # : 'E.g. wholesale.sandbox1.nuorder.com for sandbox'
    consumer_key = None,        # : 'The consumer key to use'
    consumer_secret = None,     # : 'The oauth shared secret to use'
    oauth_token = None,         # : 'OAuth token'
    oauth_token_secret = None,  # : 'OAuth token secret'
    config_section = 'sandbox', # : 'The name of the config section to get settings from.'
    log_level = None,           # : 'The log level to use.'
    dry_run = False             # : "Don't actually run command, just show what would be run."
):
    """Make a GET request to NuOrder"""
    _set_log_level(log_level)

    c = functools.partial(ini_config.get, config_section)

    nu = nuorder.NuOrder(
        hostname=hostname or c('hostname'),
        consumer_key=consumer_key or c('consumer_key'),
        consumer_secret=consumer_secret or c('consumer_secret'),
        oauth_token=oauth_token or c('oauth_token'),
        oauth_token_secret=oauth_token_secret or c('oauth_token_secret'),
    )
    resp_json = nu.get(endpoint=endpoint, dry_run=dry_run)
    return json.dumps(resp_json, indent=2)


@argh.wrap_errors(DEFAULT_WRAPPED_ERRORS, processor=_failure)
@argh.arg('-c', '--config-section')
@argh.arg('-d', '--data')
@argh.arg('--dry-run')
def post(
    endpoint,                   # : 'The endpoint to interact with.'
    hostname = None,            # : 'E.g. wholesale.sandbox1.nuorder.com for sandbox'
    consumer_key = None,        # : 'The consumer key to use'
    consumer_secret = None,     # : 'The oauth shared secret to use'
    oauth_token = None,         # : 'OAuth token'
    oauth_token_secret = None,  # : 'OAuth token secret'
    data = None,                # : 'The data to send along with POST/PUT. If `-` then read from stdin.'
    config_section = 'sandbox', # : 'The name of the config section to get settings from.'
    log_level = None,           # : 'The log level to use.'
    dry_run = False,            # : "Don't actually run command, just show what would be run."
    gzip_data = False           # : "Gzip data to NuOrder"
):
    """Make a POST request to NuOrder"""
    _set_log_level(log_level)

    c = functools.partial(ini_config.get, config_section)

    if data == '-':
        data = sys.stdin.buffer.read()

    nu = nuorder.NuOrder(
        hostname=hostname or c('hostname'),
        consumer_key=consumer_key or c('consumer_key'),
        consumer_secret=consumer_secret or c('consumer_secret'),
        oauth_token=oauth_token or c('oauth_token'),
        oauth_token_secret=oauth_token_secret or c('oauth_token_secret'),
    )
    resp_json = nu.post(
        endpoint,
        data,
        dry_run=dry_run,
        gzip_data=gzip_data,
    )
    return json.dumps(resp_json, indent=2)


@argh.wrap_errors(DEFAULT_WRAPPED_ERRORS, processor=_failure)
@argh.arg('-c', '--config-section')
@argh.arg('-d', '--data')
@argh.arg('--dry-run')
def put(
    endpoint,                   # : 'The endpoint to interact with.'
    hostname = None,            # : 'E.g. wholesale.sandbox1.nuorder.com for sandbox'
    consumer_key = None,        # : 'The consumer key to use'
    consumer_secret = None,     # : 'The oauth shared secret to use'
    oauth_token = None,         # : 'OAuth token'
    oauth_token_secret = None,  # : 'OAuth token secret'
    data = None,                # : 'The data to send along with POST/PUT. If `-` then read from stdin.'
    config_section = 'sandbox', # : 'The name of the config section to get settings from.'
    log_level = None,           # : 'The log level to use.'
    dry_run = False,            # : "Don't actually run command, just show what would be run."
    gzip_data = False           # : "Gzip data to NuOrder"
):
    """Make a PUT request to NuOrder"""
    _set_log_level(log_level)

    c = functools.partial(ini_config.get, config_section)

    if data == '-':
        data = sys.stdin.buffer.read()

    nu = nuorder.NuOrder(
        hostname=hostname or c('hostname'),
        consumer_key=consumer_key or c('consumer_key'),
        consumer_secret=consumer_secret or c('consumer_secret'),
        oauth_token=oauth_token or c('oauth_token'),
        oauth_token_secret=oauth_token_secret or c('oauth_token_secret'),
    )
    resp_json = nu.put(
        endpoint,
        data,
        dry_run=dry_run,
        gzip_data=gzip_data,
    )
    return json.dumps(resp_json, indent=2)


command_parser = argh.ArghParser(description=__doc__)
command_parser.add_commands([
    initiate,
    interact,
    get,
    delete,
    post,
    put,
])
main = command_parser.dispatch
