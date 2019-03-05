# -*- coding: utf-8 -*-
from alita.utils import escape
from alita.constants import *
from alita.base import BaseHTTPException, BaseResponse


class HTTPException(BaseHTTPException):
    def get_description(self, environ=None):
        """
        Get the description.
        """
        return HTTP_EXCEPTION_DESCRIPTION.format(
            description=escape(self.description)
        )

    def get_body(self, environ=None):
        """
        Get the HTML body.
        """
        return HTTP_EXCEPTION_TEMPLATE.format(
            code=self.code,
            name=escape(self.name.decode()),
            description=self.get_description(environ)
        )

    def get_headers(self, environ=None):
        """
        Get a list of headers.
        """
        return [('Content-Type', 'text/html')]

    def get_response(self, environ=None):
        """Get a response object.  If one was passed to the exception
        it's returned directly.

        :param environ: the optional environ for the request.  This
                        can be used to modify the response depending
                        on how the request looked like.
        :return: a :class:`Response` object or a subclass thereof.
        """
        if self.response is not None:
            return self.response
        headers = self.get_headers(environ)
        return BaseResponse(
            self.get_body(environ),
            self.code, headers,
            "text/html; charset=utf-8"
        )


class BadRequest(HTTPException):

    """
    *400* `Bad Request`

    Raise if the browser sends something to the application the application
    or server cannot handle.
    """
    code = 400
    description = (
        'The browser (or proxy) sent a request that this server could '
        'not understand.'
    )


class ClientDisconnected(BadRequest):

    """
    Internal exception that is raised if Werkzeug detects a disconnected
    client.  Since the client is already gone at that point attempting to
    send the error message to the client might not work and might ultimately
    result in another exception in the server.  Mainly this is here so that
    it is silenced by default as far as Werkzeug is concerned.

    Since disconnections cannot be reliably detected and are unspecified
    by WSGI to a large extent this might or might not be raised if a client
    is gone.

    .. versionadded:: 0.8
    """


class SecurityError(BadRequest):

    """
    Raised if something triggers a security error.  This is otherwise
    exactly like a bad request error.

    .. versionadded:: 0.9
    """


class BadHost(BadRequest):

    """
    Raised if the submitted host is badly formatted.

    .. versionadded:: 0.11.2
    """


class Unauthorized(HTTPException):

    """*401* `Unauthorized`

    Raise if the user is not authorized.  Also used if you want to use HTTP
    basic auth.
    """
    code = 401
    description = (
        'The server could not verify that you are authorized to access '
        'the URL requested.  You either supplied the wrong credentials (e.g. '
        'a bad password), or your browser doesn\'t understand how to supply '
        'the credentials required.'
    )


class Forbidden(HTTPException):

    """*403* `Forbidden`

    Raise if the user doesn't have the permission for the requested resource
    but was authenticated.
    """
    code = 403
    description = (
        'You don\'t have the permission to access the requested resource. '
        'It is either read-protected or not readable by the server.'
    )


class NotFound(HTTPException):

    """*404* `Not Found`

    Raise if a resource does not exist and never existed.
    """
    code = 404
    description = (
        'The requested URL was not found on the server.  '
        'If you entered the URL manually please check your spelling and '
        'try again.'
    )


class MethodNotAllowed(HTTPException):

    """*405* `Method Not Allowed`

    Raise if the server used a method the resource does not handle.  For
    example `POST` if the resource is view only.  Especially useful for REST.

    The first argument for this exception should be a list of allowed methods.
    Strictly speaking the response would be invalid if you don't provide valid
    methods in the header which you can do with that list.
    """
    code = 405
    description = 'The method is not allowed for the requested URL.'

    def __init__(self, valid_methods=None, description=None):
        HTTPException.__init__(self, description)
        self.valid_methods = valid_methods

    def get_headers(self, environ):
        headers = HTTPException.get_headers(self, environ)
        if self.valid_methods:
            headers.append(('Allow', ', '.join(self.valid_methods)))
        return headers


class NotAcceptable(HTTPException):

    """*406* `Not Acceptable`

    Raise if the server can't return any content conforming to the
    `Accept` headers of the client.
    """
    code = 406

    description = (
        'The resource identified by the request is only capable of '
        'generating response entities which have content characteristics '
        'not acceptable according to the accept headers sent in the '
        'request.'
    )


class RequestTimeout(HTTPException):

    """*408* `Request Timeout`

    Raise to signalize a timeout.
    """
    code = 408
    description = (
        'The server closed the network connection because the browser '
        'didn\'t finish the request within the specified time.'
    )


class Conflict(HTTPException):

    """*409* `Conflict`

    Raise to signal that a request cannot be completed because it conflicts
    with the current state on the server.

    .. versionadded:: 0.7
    """
    code = 409
    description = (
        'A conflict happened while processing the request.  The resource '
        'might have been modified while the request was being processed.'
    )


class Gone(HTTPException):

    """*410* `Gone`

    Raise if a resource existed previously and went away without new location.
    """
    code = 410
    description = (
        'The requested URL is no longer available on this server and there '
        'is no forwarding address. If you followed a link from a foreign '
        'page, please contact the author of this page.'
    )


class LengthRequired(HTTPException):

    """*411* `Length Required`

    Raise if the browser submitted data but no ``Content-Length`` header which
    is required for the kind of processing the server does.
    """
    code = 411
    description = (
        'A request with this method requires a valid <code>Content-'
        'Length</code> header.'
    )


class PreconditionFailed(HTTPException):

    """*412* `Precondition Failed`

    Status code used in combination with ``If-Match``, ``If-None-Match``, or
    ``If-Unmodified-Since``.
    """
    code = 412
    description = (
        'The precondition on the request for the URL failed positive '
        'evaluation.'
    )


class RequestEntityTooLarge(HTTPException):

    """*413* `Request Entity Too Large`

    The status code one should return if the data submitted exceeded a given
    limit.
    """
    code = 413
    description = (
        'The data value transmitted exceeds the capacity limit.'
    )


class RequestURITooLarge(HTTPException):

    """*414* `Request URI Too Large`

    Like *413* but for too long URLs.
    """
    code = 414
    description = (
        'The length of the requested URL exceeds the capacity limit '
        'for this server.  The request cannot be processed.'
    )


class UnsupportedMediaType(HTTPException):

    """*415* `Unsupported Media Type`

    The status code returned if the server is unable to handle the media type
    the client transmitted.
    """
    code = 415
    description = (
        'The server does not support the media type transmitted in '
        'the request.'
    )


class RequestedRangeNotSatisfiable(HTTPException):

    """*416* `Requested Range Not Satisfiable`

    The client asked for an invalid part of the file.

    .. versionadded:: 0.7
    """
    code = 416
    description = (
        'The server cannot provide the requested range.'
    )

    def __init__(self, length=None, units="bytes", description=None):
        """Takes an optional `Content-Range` header value based on ``length``
        parameter.
        """
        HTTPException.__init__(self, description)
        self.length = length
        self.units = units

    def get_headers(self, environ):
        headers = HTTPException.get_headers(self, environ)
        if self.length is not None:
            headers.append(
                ('Content-Range', '%s */%d' % (self.units, self.length)))
        return headers


class ExpectationFailed(HTTPException):

    """*417* `Expectation Failed`

    The server cannot meet the requirements of the Expect request-header.

    .. versionadded:: 0.7
    """
    code = 417
    description = (
        'The server could not meet the requirements of the Expect header'
    )


class ImATeapot(HTTPException):

    """*418* `I'm a teapot`

    The server should return this if it is a teapot and someone attempted
    to brew coffee with it.

    .. versionadded:: 0.7
    """
    code = 418
    description = (
        'This server is a teapot, not a coffee machine'
    )


class UnprocessableEntity(HTTPException):

    """*422* `Unprocessable Entity`

    Used if the request is well formed, but the instructions are otherwise
    incorrect.
    """
    code = 422
    description = (
        'The request was well-formed but was unable to be followed '
        'due to semantic errors.'
    )


class Locked(HTTPException):

    """*423* `Locked`

    Used if the resource that is being accessed is locked.
    """
    code = 423
    description = (
        'The resource that is being accessed is locked.'
    )


class PreconditionRequired(HTTPException):

    """*428* `Precondition Required`

    The server requires this request to be conditional, typically to prevent
    the lost update problem, which is a race condition between two or more
    clients attempting to update a resource through PUT or DELETE. By requiring
    each client to include a conditional header ("If-Match" or "If-Unmodified-
    Since") with the proper value retained from a recent GET request, the
    server ensures that each client has at least seen the previous revision of
    the resource.
    """
    code = 428
    description = (
        'This request is required to be conditional; try using "If-Match" '
        'or "If-Unmodified-Since".'
    )


class TooManyRequests(HTTPException):

    """*429* `Too Many Requests`

    The server is limiting the rate at which this user receives responses, and
    this request exceeds that rate. (The server may use any convenient method
    to identify users and their request rates). The server may include a
    "Retry-After" header to indicate how long the user should wait before
    retrying.
    """
    code = 429
    description = (
        'This user has exceeded an allotted request count. Try again later.'
    )


class RequestHeaderFieldsTooLarge(HTTPException):

    """*431* `Request Header Fields Too Large`

    The server refuses to process the request because the header fields are too
    large. One or more individual fields may be too large, or the set of all
    headers is too large.
    """
    code = 431
    description = (
        'One or more header fields exceeds the maximum size.'
    )


class UnavailableForLegalReasons(HTTPException):

    """*451* `Unavailable For Legal Reasons`

    This status code indicates that the server is denying access to the
    resource as a consequence of a legal demand.
    """
    code = 451
    description = (
        'Unavailable for legal reasons.'
    )


class InternalServerError(HTTPException):

    """*500* `Internal Server Error`

    Raise if an internal server error occurred.  This is a good fallback if an
    unknown error occurred in the dispatcher.
    """
    code = 500
    description = (
        'The server encountered an internal error and was unable to '
        'complete your request.  Either the server is overloaded or there '
        'is an error in the application.'
    )


class NotImplemented(HTTPException):

    """*501* `Not Implemented`

    Raise if the application does not support the action requested by the
    browser.
    """
    code = 501
    description = (
        'The server does not support the action requested by the '
        'browser.'
    )


class BadGateway(HTTPException):

    """*502* `Bad Gateway`

    If you do proxying in your application you should return this status code
    if you received an invalid response from the upstream server it accessed
    in attempting to fulfill the request.
    """
    code = 502
    description = (
        'The proxy server received an invalid response from an upstream '
        'server.'
    )


class ServiceUnavailable(HTTPException):

    """*503* `Service Unavailable`

    Status code you should return if a service is temporarily unavailable.
    """
    code = 503
    description = (
        'The server is temporarily unable to service your request due to '
        'maintenance downtime or capacity problems.  Please try again '
        'later.'
    )


class GatewayTimeout(HTTPException):

    """*504* `Gateway Timeout`

    Status code you should return if a connection to an upstream server
    times out.
    """
    code = 504
    description = (
        'The connection to an upstream server timed out.'
    )


class HTTPVersionNotSupported(HTTPException):

    """*505* `HTTP Version Not Supported`

    The server does not support the HTTP protocol version used in the request.
    """
    code = 505
    description = (
        'The server does not support the HTTP protocol version used in the '
        'request.'
    )


default_exceptions = {}
__all__ = ['HTTPException']


def _find_exceptions():
    for name, obj in iter(globals().items()):
        try:
            is_http_exception = issubclass(obj, HTTPException)
        except TypeError:
            is_http_exception = False
        if not is_http_exception or obj.code is None:
            continue
        __all__.append(obj.__name__)
        old_obj = default_exceptions.get(obj.code, None)
        if old_obj is not None and issubclass(obj, old_obj):
            continue
        default_exceptions[obj.code] = obj


_find_exceptions()
del _find_exceptions


class Aborter(object):

    """
    When passed a dict of code -> exception items it can be used as
    callable that raises exceptions.  If the first argument to the
    callable is an integer it will be looked up in the mapping, if it's
    a WSGI application it will be raised in a proxy exception.

    The rest of the arguments are forwarded to the exception constructor.
    """

    def __init__(self, mapping=None, extra=None):
        if mapping is None:
            mapping = default_exceptions
        self.mapping = dict(mapping)
        if extra is not None:
            self.mapping.update(extra)

    def __call__(self, code, *args, **kwargs):
        if not args and not kwargs and not isinstance(code, int):
            raise HTTPException(response=code)
        if code not in self.mapping:
            raise LookupError('no exception for %r' % code)
        raise self.mapping[code](*args, **kwargs)


def abort(status, *args, **kwargs):
    '''
    Raises an :py:exc:`HTTPException` for the given status code or WSGI
    application::

        abort(404)  # 404 Not Found
        abort(Response('Hello World'))

    Can be passed a WSGI application or a status code.  If a status code is
    given it's looked up in the list of exceptions and will raise that
    exception, if passed a WSGI application it will wrap it in a proxy WSGI
    exception and raise that::

       abort(404)
       abort(Response('Hello World'))

    '''
    return Aborter()(status, *args, **kwargs)


#: an exception that is used internally to signal both a key error and a
#: bad request.  Used by a lot of the datastructures.
BadRequestKeyError = BadRequest.wrap(KeyError)


class MiddlewareNotUsed(Exception):
    """
    This middleware is not used in this server configuration
    """
    pass
