import http

import flask

from .. import events


blueprint = flask.Blueprint('downloads', __name__)


@blueprint.get('/<path:path>')
def file_download(*, path):
    download_directory = flask.current_app.config['DOWNLOADS']
    if not download_directory:
        flask.abort(http.HTTPStatus.INTERNAL_SERVER_ERROR)

    response = flask.send_from_directory(
        download_directory, path, as_attachment=True)

    flask.current_app.logger.info(
        events.Source.EYETEA_DOWNLOAD.value,
        extra={
            'response': response,
            'source': events.Source.EYETEA_DOWNLOAD})

    return response

