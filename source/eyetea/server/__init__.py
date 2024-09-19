import argparse
import logging
import logging.handlers

import flask
import werkzeug.exceptions

# TODO: figure out what to do with imports
#       (i.e. when from <x> import <y> is ok)
from . import downloads, pastables, shells, uploads
from .. import events, utilities


def after_request(response):
    flask.current_app.logger.info(
        events.Source.HTTP_REQUEST.value,
        extra={
            'level': events.Level.INFO,
            'source': events.Source.HTTP_REQUEST,
            'response': response})

    if response.status_code > 399:
        level = events.Level.ERROR
        logger = flask.current_app.logger.error
    else:
        level = events.Level.SUCCESS
        logger = flask.current_app.logger.info

    logger(
        events.Source.HTTP_RESPONSE.value,
        extra={
            'level': level,
            'source': events.Source.HTTP_RESPONSE,
            'response': response})

    return response

def error_handler(error):
    # triggers `after_request()` for error responses
    return error.get_response()


def create_server(config=None):
    server = flask.Flask(__name__)

    if isinstance(config, argparse.Namespace):
        server.config.update({
            key.upper(): value for key, value in vars(config).items()})
    elif isinstance(config, dict):
        server.config.from_mapping(config)
    elif config is not None:
        server.config.from_object(config)

    queue_handler = logging.handlers.QueueHandler(server.config['QUEUE'])
    queue_handler.setFormatter(events.RequestFormatter())

    server.logger.setLevel(logging.INFO)
    server.logger.addHandler(queue_handler)

    server.add_template_filter(utilities.powershell_encode)
    server.add_template_global(utilities.strings_random)

    server.register_blueprint(pastables.blueprint)
    server.register_blueprint(shells.blueprint, url_prefix='/sh')

    if server.config['DOWNLOADS']:
        server.register_blueprint(
            downloads.blueprint, url_prefix='/dl')

    if server.config['UPLOADS']:
        server.register_blueprint(
            uploads.blueprint, url_prefix='/ul')

    server.after_request(after_request)
    server.register_error_handler(
        werkzeug.exceptions.HTTPException, error_handler)

    return server

