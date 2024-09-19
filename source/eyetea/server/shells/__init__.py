import flask

# TODO: figure out what to do with imports
#       (i.e. when from <x> import <y> is ok)
from . import reverse, utilities


blueprint = flask.Blueprint('shells', __name__)

blueprint.register_blueprint(reverse.blueprint, url_prefix='/r')
blueprint.register_blueprint(utilities.blueprint, url_prefix='/u')

