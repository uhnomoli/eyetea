import argparse
import logging
import multiprocessing

import flask

from . import server, ui, utilities


def main():
    parser = argparse.ArgumentParser(
        prog='eyetea',
        description='A pentesting tool that streamlines data transfer and shell access')

    parser.add_argument('-a', '--auto',
        action='store_true',
        help='Automatically start a listener for reverse shell payloads')
    parser.add_argument('-d', '--downloads',
        default=None, type=utilities.Path,
        help='Local path downloads should be served from')
    parser.add_argument('-l', '--local',
        type=utilities.HostPort,
        help='Default host and port used in reverse shell payloads')
    parser.add_argument('-u', '--uploads',
        default=None, type=utilities.Path,
        help='Local path uploads should be stored at')
    parser.add_argument('host',
        type=utilities.HostSpecified,
        help='Host the server will listen on')
    parser.add_argument('port',
        default=8080, nargs='?', type=utilities.Port,
        help='Port the server will listen on')

    options = parser.parse_args()
    if options.local is None:
        options.local = utilities.HostPort(f'{options.host}:54321')

    options.queue = multiprocessing.Queue()

    ui.UI(options, server.create_server(options)).run()
    #server.create_server(options).run(host=options.host, port=options.port, use_reloader=False)

if __name__ == '__main__':
    main()

