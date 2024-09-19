import flask

from .. import events


blueprint = flask.Blueprint('pastables', __name__)


@blueprint.get('/p<context>/<path:path>')
def pastable_request(*, context, path):
    with flask.current_app.test_request_context(f'/{path}',
            headers={'User-Agent': 'eyetea'}):
        endpoint = flask.request.url_rule.endpoint
        kwargs = flask.request.view_args

        response = flask.current_app.view_functions[endpoint](
            context=context, test=True, **kwargs)

    flask.current_app.logger.info(
        events.Source.EYETEA_PASTABLE.value,
        extra={
            'response': response,
            'source': events.Source.EYETEA_PASTABLE})

    return response

