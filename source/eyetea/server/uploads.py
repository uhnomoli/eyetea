import base64
import binascii
import http
import os.path

import flask

from .. import events, utilities


blueprint = flask.Blueprint('uploads', __name__)


@blueprint.route('', methods=['GET','POST'])
def file_upload():
    upload_directory = flask.current_app.config['UPLOADS']
    if not upload_directory:
        flask.abort(http.HTTPStatus.INTERNAL_SERVER_ERROR)

    if flask.request.method == 'POST':
        for _, file in flask.request.files.items(multi=True):
            file.save(utilities.path_secure(upload_directory, file.filename))
    else:
        for filename, data in flask.request.args.items():
            try:
                data = base64.urlsafe_b64decode(data)
            except binascii.Error:
                flask.abort(http.HTTPStatus.BAD_REQUEST)

            path = utilities.path_secure(upload_directory, filename)
            with open(path, 'wb') as fd:
                fd.write(data)

    response = flask.Response(status=http.HTTPStatus.NO_CONTENT)

    flask.current_app.logger.info(
        events.Source.EYETEA_UPLOAD.value,
        extra={
            'response': response,
            'source': events.Source.EYETEA_UPLOAD})

    return response

