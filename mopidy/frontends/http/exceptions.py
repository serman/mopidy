from mopidy.exceptions import MopidyException


class HttpError(MopidyException):
    """See fields on this class for available MPD error codes"""

    HTTP_ERROR_NO_EXIST = 50
    HTTP_ERROR_WRONG_PARAMETER = 50
    error_code = 0

    def __init__(self, message=u'', index=0, command=u''):
        super(MpdAckError, self).__init__(message, index, command)
        self.message = message
        self.index = index
        self.command = command
        

    def get_http_error(self):
        """
        MPD error code format::

            ACK [%(error_code)i@%(index)i] {%(command)s} description
        """
        return u'ACK [%i@%i] {%s} %s' % (
            self.__class__.error_code, self.index, self.command, self.message)


class HttpNoExistError(HttpError):
    error_code = HttpError.HTTP_ERROR_NO_EXIST

class HttpWrongParameterError(HttpError):
    error_code = HttpError.HTTP_ERROR_WRONG_PARAMETER
