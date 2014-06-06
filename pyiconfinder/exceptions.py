class IconfinderError(Exception):
    """Iconfinder API error.

    Base exception class for all Iconfinder API wrapper exceptions.
    """

    pass


class PermissionDeniedError(IconfinderError):
    """Permission denied error.
    """

    pass


class InsufficientPermissionsError(PermissionDeniedError):
    """Insufficient permissions error.

    Make sure the authentication was performed with the scope necessary to
    access the resource.
    """

    pass


class NotPurchasedError(IconfinderError):
    """Error indicating that the requested resource has not been purchased.

    Occurs when trying to access premium resources which have not been
    purchased by the authenticated user.
    """

    pass


class NotFoundError(IconfinderError):
    """Error indicating that the requested resource was not found.
    """

    pass


class RateLimitExceededError(IconfinderError):
    """API rate limit exceeded error.
    """

    pass


class InternalServerError(IconfinderError):
    """Internal API server error.
    """

    pass


class BadCredentialsError(IconfinderError):
    """Bad credentials error.
    """

    pass


class BadRequestError(IconfinderError):
    """Bad request error.
    """

    pass


class InvalidParameterError(BadRequestError):
    """Invalid parameter error.

    :ivar parameter: Errorneous parameter.
    """

    def __init__(self, message, parameter):
        self.parameter = parameter
        super(InvalidParameterError, self).__init__(message)


class UnexpectedResponseError(IconfinderError):
    """Unexpected response error.
    """

    pass
