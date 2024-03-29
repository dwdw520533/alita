import json
from alita.base import BaseRequest
from alita.exceptions import BadRequest


class JSONMixin(object):
    """
    Common mixin for both request and response objects to provide JSON
    """
    _cached_json = (Ellipsis, Ellipsis)

    @property
    def is_json(self):
        mt = self.content_type
        return (
            mt == 'application/json'
            or (mt.startswith('application/')) and mt.endswith('+json')
        )

    @property
    def json(self):
        return self.get_json()

    def _get_data_for_json(self, cache):
        return self.get_data(cache=cache)

    def get_json(self, force=False, silent=False, cache=True):
        if cache and self._cached_json[silent] is not Ellipsis:
            return self._cached_json[silent]

        if not (force or self.is_json):
            return None

        data = self._get_data_for_json(cache=cache)

        try:
            rv = json.loads(data)
        except ValueError as e:
            if silent:
                rv = None
                if cache:
                    normal_rv, _ = self._cached_json
                    self._cached_json = (normal_rv, rv)
            else:
                rv = self.on_json_loading_failed(e)
                if cache:
                    _, silent_rv = self._cached_json
                    self._cached_json = (rv, silent_rv)
        else:
            if cache:
                self._cached_json = (rv, rv)
        return rv

    def on_json_loading_failed(self, ex):
        raise BadRequest('Failed to decode JSON object: {0}'.format(ex))


class Request(BaseRequest, JSONMixin):
    route_match = None
    routing_exception = None

    def __init__(self, app, environ, headers=None):
        super(Request, self).__init__(app, environ, headers)
        self.match_request()

    def match_request(self):
        try:
            self.route_match = self.app.router.match(self)
        except self.app.exception_class as ex:
            self.routing_exception = ex
        except Exception as ex:
            self.routing_exception = BadRequest(str(ex))

    @property
    def endpoint(self):
        return self.route_match.endpoint if self.route_match else None

    @property
    def blueprint(self):
        """
        The name of the current blueprint
        """
        if self.route_match and '.' in self.route_match.endpoint:
            return self.route_match.endpoint.rsplit('.', 1)[0]
