import enum
import logging
import logging.handlers

import flask
import werkzeug.utils


class Level(enum.StrEnum):
    ERROR = 'error'
    INFO = 'info'
    SUCCESS = 'success'

class Source(enum.StrEnum):
    EYETEA_DOWNLOAD = 'eyetea_download'
    EYETEA_PASTABLE = 'eyetea_pastable'
    EYETEA_REVERSE_SHELL = 'eyetea_reverse_shell'
    EYETEA_UPLOAD = 'eyetea_upload'
    EYETEA_UTILITIES = 'eyetea_utilities'
    HTTP_REQUEST = 'http_request'
    HTTP_RESPONSE = 'http_response'
    INTERNAL = 'internal'
    UNKNOWN = 'unknown'


class RequestFormatter(logging.Formatter):
    def format(self, record):
        request = {
            'base_url': None,
            'cookies': {},
            'files': [],
            'headers': [],
            'host': None,
            'method': None,
            'user_agent': None,
            'url': {},
            'values': {}}
        response = {
            'headers': [],
            'status': None,
            'status_code': None}

        if flask.has_request_context():
            request['base_url'] = flask.request.base_url
            request['cookies'] = flask.request.cookies.to_dict(flat=False)
            request['headers'] = flask.request.headers.to_wsgi_list()
            request['host'] = flask.request.host
            request['method'] = flask.request.method
            request['remote_addr'] = flask.request.remote_addr
            request['user_agent'] = flask.request.user_agent.string
            request['url'] = {
                'root_url': flask.request.root_url,
                'path': flask.request.path,
                'query_string': flask.request.query_string.decode(
                    'utf-8', errors='replace')}
            request['values'] = flask.request.values.to_dict(flat=False)

            request['files'] = []
            for _, file in flask.request.files.items(multi=True):
                request['files'].append({
                    'filename': werkzeug.utils.secure_filename(file.filename),
                    'length': len(file.getbuffer()),
                    'mimetype': file.mimetype,
                    'name': file.name})

        if hasattr(record, 'response'):
            response['headers'] = record.response.headers.to_wsgi_list()
            response['status'] = record.response.status
            response['status_code'] = record.response.status_code

            delattr(record, 'response')

        record.data = {
            'request': request,
            'response': response}

        record.level = getattr(record, 'level', None)
        if not isinstance(record.level, Level):
            record.level = Level.INFO

        record.source = getattr(record, 'source', None)
        if not isinstance(record.source, Source):
            record.source = Source.UNKNOWN
        elif ('User-Agent', 'eyetea') in request['headers']:
            record.source = Source.INTERNAL

        return super().format(record)

