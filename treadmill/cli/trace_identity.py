"""Treadmill identity trace CLI.
"""

import logging
import sys

import click

from treadmill import cli
from treadmill.websocket import client as ws_client


_LOGGER = logging.getLogger(__name__)


def init():
    """Return top level command handler."""

    ctx = {}

    @click.command()
    @click.option('--cell', required=True,
                  envvar='TREADMILL_CELL',
                  callback=cli.handle_context_opt,
                  expose_value=False)
    @click.option('--api', required=False, help='REST API url to use.',
                  metavar='URL',
                  envvar='TREADMILL_RESTAPI')
    @click.option('--wsapi', required=False, help='WebSocket API url to use.',
                  metavar='URL',
                  envvar='TREADMILL_WSAPI')
    @click.option('--snapshot', is_flag=True, default=False)
    @click.argument('identity-group')
    def trace(api, wsapi, snapshot, identity_group):
        """Trace identity group events.

        Invoking treadmill_trace with non existing application instance will
        cause the utility to wait for the specified instance to be started.

        Specifying already finished instance of the application will display
        historical trace information and exit status.

        Specifying only an application name will list all the instance IDs with
        trace information available.
        """
        # Disable too many branches.
        #
        # pylint: disable=R0912

        ctx['api'] = api
        ctx['wsapi'] = wsapi

        def on_message(result):
            """Callback to process trace message."""
            host = result.get('host')
            if host is None:
                host = ''
            app = result.get('app')
            if app is None:
                app = ''

            identity_group = result['identity-group']
            identity = result['identity']

            print('{identity_group}/{identity} {app} {host}'.format(
                identity_group=identity_group,
                identity=identity,
                app=app,
                host=host
            ))

            return True

        def on_error(result):
            """Callback to process errors."""
            click.echo('Error: %s' % result['_error'], err=True)

        try:
            return ws_client.ws_loop(
                ctx['wsapi'],
                {'topic': '/identity-groups',
                 'identity-group': identity_group},
                snapshot,
                on_message,
                on_error
            )
        except ws_client.ConnectionError:
            click.echo('Could not connect to any Websocket APIs', err=True)
            sys.exit(-1)

    return trace