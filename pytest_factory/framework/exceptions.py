from typing import Any, Callable

from pytest_factory.logger import get_logger

logger = get_logger(__name__)


class PytestFactoryBaseException(Exception):
    """
    base exception for exceptions that occur within the framework. not to be used directly; inherit from this class instead
    NOTE __init__() will ALSO log out the exception description (i.e. self.log_msg) so you don't need to do it as a
    separate action!
    """

    def __init__(self, log_error: bool = True, *args, **kwargs):
        """
        :param log_msg: str message to send to logger;
        :param log_error: bool, if True (default) sends log_msg to logger.error, else logger.warning;
        note this does NOT determine if exception is raised or not! that must be decided by the user
        """
        if log_error:
            self.log_msg = self.get_error_msg(*args, **kwargs)
            logger.error(msg=self.log_msg)
        else:
            self.log_msg = self.get_warning_msg(*args, **kwargs)
            logger.warning(msg=self.log_msg)

    def get_warning_msg(self, *args, **kwargs) -> str:
        raise NotImplementedError

    def get_error_msg(self, *args, **kwargs) -> str:
        raise NotImplementedError

    def __str__(self):
        return self.log_msg


class ConfigException(PytestFactoryBaseException):
    def get_error_msg(self, log_msg: str) -> str:
        return log_msg


class MissingHandlerException(PytestFactoryBaseException):
    def get_error_msg(self) -> str:
        log_msg = 'this test case is missing a mock_request or similar factory! no RequestHandler defined to test!'
        return log_msg


class TestDoubleTypeException(PytestFactoryBaseException):
    def get_error_msg(self, response: Any, request_module_name: str) -> str:
        log_msg = f'cannot convert test double {str(response)} of type {type(response)} into type expected by module {request_module_name}'
        return log_msg


class UnhandledPluginException(PytestFactoryBaseException):
    def get_error_msg(self, plugin_name: str, exception: Exception, *args, **kwargs) -> str:
        log_msg = f'unhandled exception in plugin {plugin_name}: {exception}'
        return log_msg


class RequestNormalizationException(PytestFactoryBaseException):
    def get_error_msg(self, req_obj_cls: Callable, method: str, path: str, ex: Exception, *args, **kwargs) -> str:
        qwargs = {
            "method": method,
            "path": path,
            **kwargs
        }
        log_msg = f'while creating {req_obj_cls} with kwargs: {qwargs}, encountered unhandled exception: {ex}'
        return log_msg


class MissingFactoryException(PytestFactoryBaseException):
    def get_error_msg(self, factory_name: str, *_, **__) -> str:
        log_msg = f'this test case is missing the requested factory: {factory_name}! '
        return log_msg


class MissingTestDoubleException(PytestFactoryBaseException):
    """
    exception for when Store cannot find the expected test double; this can indicate either a test code error in
    setting up the factories OR an error in component under test not forming the request correctly
    """

    def get_error_msg(self, req_obj: 'BaseMockRequest') -> str:
        return f"could not find test double match for request signature: {req_obj}!"


class UnCalledTestDoubleException(PytestFactoryBaseException):
    def get_error_msg(self, uncalled_test_doubles: dict) -> str:
        return f"the following test doubles were NOT used in this test: {uncalled_test_doubles}"

    def get_warning_msg(self, uncalled_test_doubles: dict):
        warning_msg = " if this is not expected, set assert_no_missing_calls to True"
        return self.get_error_msg(uncalled_test_doubles=uncalled_test_doubles) + warning_msg


class OverCalledTestDoubleException(PytestFactoryBaseException):
    def get_error_msg(self, mock_responses: list, req_obj: Any) -> str:
        return f'expected only {len(mock_responses)} calls to {req_obj}!'

    def get_warning_msg(self, mock_responses: list, req_obj: Any) -> str:
        warning_msg = f" will repeat last response: {mock_responses[-1][1]}"
        return self.get_error_msg(mock_responses=mock_responses, req_obj=req_obj) + warning_msg
